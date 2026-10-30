"""Orthographic globe renderer (numpy + OpenCV) with orbit propagation and overlays."""
import functools
import math
import os

import cv2
import numpy as np

from common_paths import CACHE, WORK
from render.base import (AMBER, CYAN, H, INK, MUTED, Scene, W, draw_text, ease_io, font, starfield, to_np,
                         to_pil, vignette)

RE = 6371.0
D2R = math.pi / 180


@functools.lru_cache(None)
def earth_texture(kind="day"):
    path = os.path.join(CACHE, f"tex_{kind}.npy")
    if os.path.exists(path):
        return np.load(path)
    src = os.path.join(WORK, "dl/ne/NE1_50M_SR_W/NE1_50M_SR_W.tif")
    im = cv2.imread(src, cv2.IMREAD_COLOR)[..., ::-1]
    im = cv2.resize(im, (8192, 4096), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    if kind == "day":
        # deepen oceans and add a little contrast so the globe reads at night-sky exposure
        lum = im.mean(-1, keepdims=True)
        water = (im[..., 2:3] > im[..., 0:1] + 0.06).astype(np.float32)
        im = im * (1 - 0.35 * water)
        im = np.clip((im - 0.03) * 1.12, 0, 1) ** 1.1
    elif kind == "dark":
        g = im.mean(-1, keepdims=True)
        land = (im[..., 2:3] <= im[..., 0:1] + 0.06).astype(np.float32)
        base = np.array([0.035, 0.05, 0.085], np.float32)
        im = base + land * (0.10 + 0.25 * g) * np.array([0.75, 0.82, 0.95], np.float32)
    out = (np.clip(im, 0, 1) * 255).astype(np.uint8)
    np.save(path, out)
    return out


@functools.lru_cache(None)
def coast_lines(res="50m"):
    import cartopy.io.shapereader as shp
    lines = []
    for rec in shp.Reader(shp.natural_earth(resolution=res, category="physical", name="coastline")).geometries():
        geoms = getattr(rec, "geoms", [rec])
        for g in geoms:
            xy = np.asarray(g.coords)
            if len(xy) > 1:
                lines.append(xy)
    return lines


@functools.lru_cache(None)
def border_lines(res="50m"):
    import cartopy.io.shapereader as shp
    lines = []
    for rec in shp.Reader(shp.natural_earth(resolution=res, category="cultural", name="admin_0_boundary_lines_land")).geometries():
        for g in getattr(rec, "geoms", [rec]):
            xy = np.asarray(g.coords)
            if len(xy) > 1:
                lines.append(xy)
    return lines


ORBITS = {
    # altitude km, inclination deg, RAAN drift deg/day
    "oco2": (705.0, 98.2, 0.9856),
    "iss": (420.0, 51.6, -5.0),
}


def orbit_lonlat(kind, hours, lon_eq=0.0):
    """Ground track (lon, lat) and altitude ratio for a circular orbit; t=0 ascending node at lon_eq."""
    h, inc, drift = ORBITS[kind]
    a = RE + h
    T = 2 * math.pi * math.sqrt(a ** 3 / 398600.4418) / 3600.0  # hours
    t = np.asarray(hours, np.float64)
    u = 2 * math.pi * t / T
    i = inc * D2R
    raan = (lon_eq + drift * t / 24.0) * D2R
    x = np.cos(raan) * np.cos(u) - np.sin(raan) * np.sin(u) * math.cos(i)
    y = np.sin(raan) * np.cos(u) + np.cos(raan) * np.sin(u) * math.cos(i)
    z = np.sin(u) * math.sin(i)
    lon = np.degrees(np.arctan2(y, x)) - 360.0 / 23.9345 * t
    lat = np.degrees(np.arcsin(z))
    lon = (lon + 180) % 360 - 180
    return lon, lat, a / RE, T


class Globe:
    def __init__(self, texture="day"):
        self.tex = earth_texture(texture)
        self.th, self.tw = self.tex.shape[:2]

    def view(self, lon0, lat0, R, cx=W / 2, cy=H / 2):
        self.lon0, self.lat0, self.R, self.cx, self.cy = lon0, lat0, R, cx, cy
        l0, p0 = lon0 * D2R, lat0 * D2R
        self.c = np.array([math.cos(p0) * math.cos(l0), math.cos(p0) * math.sin(l0), math.sin(p0)])
        self.e = np.array([-math.sin(l0), math.cos(l0), 0.0])
        self.n = np.array([-math.sin(p0) * math.cos(l0), -math.sin(p0) * math.sin(l0), math.cos(p0)])

    def _grid(self):
        x0, x1 = max(int(self.cx - self.R) - 2, 0), min(int(self.cx + self.R) + 3, W)
        y0, y1 = max(int(self.cy - self.R) - 2, 0), min(int(self.cy + self.R) + 3, H)
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        x = (xs - self.cx) / self.R
        y = -(ys - self.cy) / self.R
        rho2 = x * x + y * y
        inside = rho2 < 1.0
        z = np.sqrt(np.clip(1 - rho2, 0, 1))
        sp, cp = math.sin(self.lat0 * D2R), math.cos(self.lat0 * D2R)
        lat = np.arcsin(np.clip(z * sp + y * cp, -1, 1))
        lon = self.lon0 * D2R + np.arctan2(x, z * cp - y * sp)
        return (x0, x1, y0, y1), inside, z, lat, lon

    def render(self, bg, overlay=None, overlay_alpha=1.0, sun=None, night_level=0.18, glow=1.0, shade=0.35, tex=None):
        """bg: HxWx3 uint8 to draw onto. overlay: equirect RGBA float [0,1] (h, w, 4)."""
        (x0, x1, y0, y1), inside, z, lat, lon = self._grid()
        tex = self.tex if tex is None else tex
        th, tw = tex.shape[:2]
        mx = (((lon / (2 * math.pi)) + 0.5) % 1.0) * tw - 0.5
        my = (0.5 - lat / math.pi) * th - 0.5
        col = cv2.remap(tex, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP).astype(np.float32)
        if overlay is not None:
            oh, ow = overlay.shape[:2]
            ox = (((lon / (2 * math.pi)) + 0.5) % 1.0) * ow - 0.5
            oy = (0.5 - lat / math.pi) * oh - 0.5
            ov = cv2.remap(overlay, ox.astype(np.float32), oy.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            a = ov[..., 3:4] * overlay_alpha
            col = col * (1 - a) + ov[..., :3] * 255 * a
        # limb darkening
        col *= (1 - shade) + shade * z[..., None] ** 0.6
        if sun is not None:
            slon, slat = sun[0] * D2R, sun[1] * D2R
            sx = math.cos(slat) * math.cos(slon)
            sy = math.cos(slat) * math.sin(slon)
            sz = math.sin(slat)
            cl = np.cos(lat)
            mu = cl * np.cos(lon) * sx + cl * np.sin(lon) * sy + np.sin(lat) * sz
            light = night_level + (1 - night_level) * np.clip((mu + 0.08) / 0.25, 0, 1)
            col *= light[..., None]
        out = bg.copy()
        region = out[y0:y1, x0:x1].astype(np.float32)
        # anti-aliased disk edge
        rr = np.sqrt(np.clip(((np.mgrid[y0:y1, x0:x1][1] - self.cx) ** 2 + (np.mgrid[y0:y1, x0:x1][0] - self.cy) ** 2), 0, None)) / self.R
        edge = np.clip((1 - rr) * self.R + 0.5, 0, 1)[..., None]
        region = region * (1 - edge) + col * edge
        out[y0:y1, x0:x1] = np.clip(region, 0, 255).astype(np.uint8)
        if glow > 0:
            out = self.atmosphere(out, glow)
        return out

    def atmosphere(self, img, strength=1.0):
        pad = int(self.R * 0.18) + 4
        x0, x1 = max(int(self.cx - self.R - pad), 0), min(int(self.cx + self.R + pad), W)
        y0, y1 = max(int(self.cy - self.R - pad), 0), min(int(self.cy + self.R + pad), H)
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        r = np.sqrt((xs - self.cx) ** 2 + (ys - self.cy) ** 2) / self.R
        outer = np.where(r >= 1, np.exp(-(r - 1) * 28), 0)
        inner = np.where(r < 1, np.clip((r - 0.86) / 0.14, 0, 1) ** 3, 0)
        g = (0.55 * outer + 0.35 * inner) * strength
        c = np.array([110, 170, 255], np.float32)
        reg = img[y0:y1, x0:x1].astype(np.float32) + g[..., None] * c
        img[y0:y1, x0:x1] = np.clip(reg, 0, 255).astype(np.uint8)
        return img

    def project(self, lon, lat, alt=1.0):
        lon, lat = np.radians(lon), np.radians(lat)
        v = np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], -1) * np.asarray(alt)[..., None]
        x, y, z = v @ self.e, v @ self.n, v @ self.c
        vis = (z > 0) | (x * x + y * y > 1.0)
        return self.cx + x * self.R, self.cy - y * self.R, vis

    def polyline(self, img, lon, lat, color, thick=2, alpha=1.0, alt=1.0, max_jump=None):
        px, py, vis = self.project(np.asarray(lon), np.asarray(lat), alt)
        segs, cur = [], []
        max_jump = max_jump or self.R * 0.5
        for i in range(len(px)):
            if vis[i] and (not cur or abs(px[i] - cur[-1][0]) + abs(py[i] - cur[-1][1]) < max_jump):
                cur.append((px[i], py[i]))
            else:
                if len(cur) > 1:
                    segs.append(cur)
                cur = [(px[i], py[i])] if vis[i] else []
        if len(cur) > 1:
            segs.append(cur)
        if not segs:
            return img
        pts = [np.round(np.array(s) * 16).astype(np.int32) for s in segs]
        return stroke(img, pts, color, thick, alpha)

    def coastlines(self, img, color=(150, 170, 200), alpha=0.6, thick=1, borders=False):
        sets = list(coast_lines()) + (list(border_lines()) if borders else [])
        allpts = []
        for xy in sets:
            px, py, vis = self.project(xy[:, 0], xy[:, 1])
            seg = []
            for i in range(len(px)):
                if vis[i]:
                    seg.append((px[i], py[i]))
                elif len(seg) > 1:
                    allpts.append(seg)
                    seg = []
                else:
                    seg = []
            if len(seg) > 1:
                allpts.append(seg)
        pts = [np.round(np.array(s) * 16).astype(np.int32) for s in allpts]
        return stroke(img, pts, color, thick, alpha)


def stroke(img, pts, color, thick=2, alpha=1.0, glow=0.0):
    """Alpha-composite anti-aliased polylines (pts in 1/16 px fixed point) onto img, working in the bounding box."""
    h, w = img.shape[:2]
    allp = np.concatenate([p.reshape(-1, 2) for p in pts if len(p)]) if pts else np.zeros((0, 2), np.int32)
    if len(allp) == 0:
        return img
    pad = int(thick + (4 + thick) * 3 + 4 if glow else thick + 3)
    x0 = max(int(allp[:, 0].min() / 16) - pad, 0)
    y0 = max(int(allp[:, 1].min() / 16) - pad, 0)
    x1 = min(int(allp[:, 0].max() / 16) + pad + 1, w)
    y1 = min(int(allp[:, 1].max() / 16) + pad + 1, h)
    if x1 <= x0 or y1 <= y0:
        return img
    mask = np.zeros((y1 - y0, x1 - x0), np.uint8)
    off = np.array([x0 * 16, y0 * 16], np.int32)
    cv2.polylines(mask, [p.reshape(-1, 2) - off for p in pts if len(p)], False, 255, thick, cv2.LINE_AA, shift=4)
    m = mask.astype(np.float32)[..., None] / 255 * alpha
    if glow:
        g = cv2.GaussianBlur(mask, (0, 0), 4 + thick).astype(np.float32)[..., None] / 255 * glow
        m = np.maximum(m, g)
    out = img.copy()
    out[y0:y1, x0:x1] = (img[y0:y1, x0:x1].astype(np.float32) * (1 - m) + np.array(color, np.float32) * m).astype(np.uint8)
    return out


def soft_glow(layer, sigma):
    """Cheap wide blur: blur at quarter resolution and upsample."""
    h, w = layer.shape[:2]
    sm = cv2.resize(layer, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    sm = cv2.GaussianBlur(sm, (0, 0), max(sigma / 4, 0.8))
    return cv2.resize(sm, (w, h), interpolation=cv2.INTER_LINEAR)


def glow_dot(img, x, y, color, r=7, halo=26, alpha=1.0):
    """Glowing marker; all work happens in a local region around (x, y)."""
    h, w = img.shape[:2]
    pad = int(halo * 3 + r + 4)
    x0, y0 = max(int(x) - pad, 0), max(int(y) - pad, 0)
    x1, y1 = min(int(x) + pad, w), min(int(y) + pad, h)
    if x1 <= x0 or y1 <= y0:
        return img
    roi = img[y0:y1, x0:x1]
    cx, cy = int(x) - x0, int(y) - y0
    layer = np.zeros_like(roi)
    cv2.circle(layer, (cx, cy), halo, color, -1, cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), halo / 2.5)
    roi2 = cv2.addWeighted(roi, 1.0, layer, 0.9 * alpha, 0)
    core = roi2.copy()
    cv2.circle(core, (cx, cy), r, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.circle(core, (cx, cy), r + 2, color, 2, cv2.LINE_AA)
    out = img.copy()
    out[y0:y1, x0:x1] = cv2.addWeighted(roi2, 1 - alpha, core, alpha, 0)
    return out


def dist_to_R(d):
    return 430.0 * 3.0 / d


class GlobeScene(Scene):
    """Generic rotating globe with optional orbits, markers, overlays."""

    texture = "day"

    def __init__(self, sc, dur):
        super().__init__(sc, dur)
        self.g = Globe(self.p.get("texture", self.texture))
        p = self.p
        self.orbit = p.get("orbit")
        if self.orbit:
            h0, h1 = p.get("orbit_hours", (0, 1))
            self.h0, self.h1 = h0, h1
            self.lon_eq = p.get("lon_eq", p.get("lon0", 0) - 25)

    def camera(self, t):
        p = self.p
        x = ease_io(t / self.dur)
        lon = p.get("lon0", 0) + (p.get("lon1", p.get("lon0", 0)) - p.get("lon0", 0)) * x
        lat = p.get("lat", 10) + (p.get("lat1", p.get("lat", 10)) - p.get("lat", 10)) * x
        d = p.get("dist", 3.0) + (p.get("dist1", p.get("dist", 3.0)) - p.get("dist", 3.0)) * x
        return lon, lat, dist_to_R(d)

    def overlay_tex(self, t):
        return None, 1.0

    def frame(self, t):
        lon, lat, R = self.camera(t)
        self.g.view(lon, lat, R)
        bg = starfield(t + hash(self.sc["id"]) % 100, drift=3)
        ov, oa = self.overlay_tex(t)
        img = self.g.render(bg, overlay=ov, overlay_alpha=oa)
        img = self.decorate(img, t)
        if self.orbit:
            img = self.draw_orbit(img, t)
        m = self.p.get("marker")
        if m:
            px, py, vis = self.g.project(np.array([m[0]]), np.array([m[1]]))
            if vis[0]:
                a = min(1.0, max(0.0, (t - 1.0) / 1.5))
                pulse = 0.5 + 0.5 * math.sin(t * 3)
                img = glow_dot(img, px[0], py[0], AMBER, r=6, halo=int(18 + 10 * pulse), alpha=a)
                im = to_pil(img)
                draw_text(im, (px[0] + 26, py[0] - 18), m[2], font(34, "Medium"), fill=INK, anchor="ls", alpha=a)
                sub = f"{abs(m[1]):.2f}°{'N' if m[1] >= 0 else 'S'}  {abs(m[0]):.2f}°{'W' if m[0] < 0 else 'E'}" + (f"  ·  {m[3]}" if len(m) > 3 else "")
                draw_text(im, (px[0] + 26, py[0] + 16), sub, font(24, "Regular"), fill=MUTED, anchor="ls", alpha=a)
                img = to_np(im)
        return vignette(img)

    def decorate(self, img, t):
        return img

    def draw_orbit(self, img, t):
        frac = t / self.dur
        hnow = self.h0 + (self.h1 - self.h0) * frac
        color = CYAN if self.orbit == "oco2" else AMBER
        if self.p.get("trail", True):
            n = max(int((hnow - self.h0) * 600), 2)
            hs = np.linspace(self.h0, hnow, n)
            lon, lat, alt, T = orbit_lonlat(self.orbit, hs, self.lon_eq)
            if self.p.get("tracks"):
                img = self.g.polyline(img, lon, lat, color, thick=2, alpha=0.55)
            else:
                img = self.g.polyline(img, lon, lat, color, thick=3, alpha=0.8)
            # orbit path in space (recent part)
            hs2 = np.linspace(max(self.h0, hnow - 0.35 * T), hnow, 200)
            lo2, la2, alt2, _ = orbit_lonlat(self.orbit, hs2, self.lon_eq)
            img = self.g.polyline(img, lo2, la2, (255, 255, 255), thick=2, alpha=0.35, alt=alt2)
        if self.p.get("sat"):
            lon, lat, alt, T = orbit_lonlat(self.orbit, np.array([hnow]), self.lon_eq)
            px, py, vis = self.g.project(lon, lat, np.array([alt]))
            if vis[0]:
                img = glow_dot(img, px[0], py[0], color, r=5, halo=22)
                im = to_pil(img)
                label = "OCO-2" if self.orbit == "oco2" else "ISS · OCO-3"
                draw_text(im, (px[0] + 20, py[0] - 14), label, font(30, "SemiBold"), fill=color, anchor="ls")
                img = to_np(im)
        if self.p.get("tracks"):
            im = to_pil(img)
            days = hnow / 24.0
            n_orb = hnow / orbit_lonlat(self.orbit, np.array([0.0]))[3]
            draw_text(im, (W - 110, H - 140), f"{days:4.1f} days", font(48, "Light"), anchor="rs")
            draw_text(im, (W - 110, H - 100), f"{n_orb:5.1f} orbits", font(28, "Regular"), fill=MUTED, anchor="rs")
            img = to_np(im)
        return img
