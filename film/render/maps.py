"""Data maps: NOAA OISST anomaly, Sentinel-5P CH4 / NO2 / CO."""
import datetime as dt
import functools
import math

import cv2
import numpy as np

from render import data
from render.base import (CO2, H, INK, MUTED, Scene, W, blank, draw_text, ease_io, font, heading, lerp, ramp, source_tag,
                         to_np, to_pil, vignette)
from render.diagrams import FlatBase
from render.globe import glow_dot


def cmap_lut(name, n=256):
    import matplotlib
    return (matplotlib.colormaps[name](np.linspace(0, 1, n))[:, :3] * 255).astype(np.float32)


def colorize(v, vmin, vmax, lut, gamma=1.0):
    x = np.clip((v - vmin) / (vmax - vmin), 0, 1) ** gamma
    idx = np.nan_to_num(x * (len(lut) - 1)).astype(np.int32)
    return lut[idx], np.isfinite(v)


def colorbar(im, x, y, w, h, lut, vmin, vmax, label, ticks, fmt="{:g}"):
    bar = np.repeat(lut[None, :, :], h, 0)
    bar = cv2.resize(bar.astype(np.uint8), (w, h))
    im.paste(to_pil(bar), (int(x), int(y)))
    for tv in ticks:
        tx = x + (tv - vmin) / (vmax - vmin) * w
        draw_text(im, (tx, y + h + 30), fmt.format(tv), font(22), fill=MUTED, anchor="ms")
    draw_text(im, (x, y - 12), label, font(24, "Medium"), fill=INK, anchor="ls")


def fill_gaps(a, sigma=3.0):
    """Normalized convolution to fill small holes in a sparse composite."""
    m = np.isfinite(a).astype(np.float32)
    v = np.nan_to_num(a)
    num = cv2.GaussianBlur(v * m, (0, 0), sigma)
    den = cv2.GaussianBlur(m, (0, 0), sigma)
    out = np.where(den > 0.15, num / np.maximum(den, 1e-6), np.nan)
    return np.where(m > 0, a, out).astype(np.float32)


# ───────────────────────────── SST ─────────────────────────────
@functools.lru_cache(None)
def sst():
    d = data.npz("oisst_anom_2014_2016.npz")
    dates = [dt.date.fromisoformat(s) for s in d["dates"]]
    return d["anom"], dates


class Sst(Scene):
    def __init__(self, sc, dur):
        super().__init__(sc, dur)
        self.anom, self.dates = sst()
        d0, d1 = dt.date.fromisoformat(self.p["d0"]), dt.date.fromisoformat(self.p["d1"])
        self.i0 = min(range(len(self.dates)), key=lambda i: abs((self.dates[i] - d0).days))
        self.i1 = min(range(len(self.dates)), key=lambda i: abs((self.dates[i] - d1).days))
        self.lut = cmap_lut("RdBu_r")
        self.fb = FlatBase(100, 300, -45, 45, (60, 170, 1860, 170 + 810))

    def frame(self, t):
        k = min(max((t - 0.8) / (self.dur - 2.0), 0), 1)
        pos = lerp(self.i0, self.i1, k)
        i = int(pos)
        f = pos - i
        a = self.anom[i].astype(np.float32)
        if f > 0 and i + 1 < len(self.anom):
            a = a * (1 - f) + self.anom[i + 1].astype(np.float32) * f
        img = self.fb.render(blank())
        # OISST: lat -89.875..89.875 ascending, lon 0.125..359.875 → flip to descending rows
        arr = np.ascontiguousarray(a[::-1])
        v = self.fb.sample(arr, 0.0, 90.0, 0.25)
        rgb, ok = colorize(v, -4, 4, self.lut)
        x0, y0, x1, y1 = self.fb.box
        reg = img[y0:y1, x0:x1].astype(np.float32)
        reg = np.where(ok[..., None], rgb * 0.95 + reg * 0.05, reg)
        img[y0:y1, x0:x1] = reg.astype(np.uint8)
        img = self.fb.coast(img, color=(40, 44, 52), alpha=0.9, thick=2)
        im = to_pil(img)
        day = self.dates[i] + dt.timedelta(days=int(round(f * 4)))
        heading(im, "Sea-surface temperature vs normal", "NOAA OISST v2.1 daily anomaly (°C), tropical Pacific", y=95)
        draw_text(im, (1840, 120), day.strftime("%d %b %Y").upper(), font(60, "Light"), anchor="rs", spacing=3)
        nx, ny = self.fb.xy(-150 + 360, 0)
        a2 = ramp(t, 3.0, 1.5)
        draw_text(im, (nx, ny - 120), "Niño 3.4 region", font(26, "Medium"), fill=INK, anchor="ms", alpha=a2 * 0.8)
        x_a, y_a = self.fb.xy(190, 5)
        x_b, y_b = self.fb.xy(240, -5)
        from PIL import ImageDraw
        dd = ImageDraw.Draw(im)
        dd.rectangle([x_a, y_a, x_b, y_b], outline=tuple(int(255 * a2 * 0.8) for _ in range(3)), width=2)
        colorbar(im, 1360, 1010, 440, 16, self.lut, -4, 4, "°C vs 1971–2000", [-4, -2, 0, 2, 4], "{:+g}")
        source_tag(im, "Data: NOAA OISST v2.1 (NOAA Open Data Dissemination on AWS)")
        return to_np(im)


# ───────────────────────────── Sentinel-5P ─────────────────────────────
REGIONS = {
    "ch4": [("South & East Asia — rice paddies and wetlands", (65, 125, 0, 42)), ("The Sudd wetlands, South Sudan", (14, 48, -6, 22)),
            ("Sahara — bright sand biases this uncorrected product high", (-15, 35, 10, 35))],
    "no2": [("Europe", (-6, 24, 40, 58)), ("Indo-Gangetic Plain", (68, 96, 18, 34)), ("Eastern China", (104, 128, 22, 42))],
}


@functools.lru_cache(None)
def land_mask(shape):
    """Land mask on a global grid from Natural Earth land polygons (cartopy shapefile)."""
    import cartopy.io.shapereader as shp
    h, w = shape
    m = np.zeros((h, w), np.uint8)
    for g in shp.Reader(shp.natural_earth(resolution="50m", category="physical", name="land")).geometries():
        for poly in getattr(g, "geoms", [g]):
            xy = np.asarray(poly.exterior.coords)
            pts = np.c_[(xy[:, 0] + 180) / 360 * w, (90 - xy[:, 1]) / 180 * h]
            cv2.fillPoly(m, [np.round(pts * 16).astype(np.int32)], 1, cv2.LINE_8, shift=4)
    m = cv2.dilate(m, np.ones((3, 3), np.uint8))
    return m.astype(bool)


@functools.lru_cache(None)
def s5p(name):
    d = data.npz(name)
    m = d["mean"].astype(np.float32)
    return m, d["bbox"], float(d["res"])


class S5pMap(Scene):
    key = "ch4"

    def __init__(self, sc, dur):
        super().__init__(sc, dur)
        if self.key == "ch4":
            m, self.bbox, self.res = s5p("s5p_ch4_2024.npz")
            lat = 90 - (np.arange(m.shape[0]) + 0.5) * self.res
            m[lat < -58] = np.nan
            m[(m < 1700) | (m > 2100)] = np.nan
            v = fill_gaps(m, 1.5)
            v = cv2.GaussianBlur(np.nan_to_num(v, nan=0), (0, 0), 1.2) / np.maximum(cv2.GaussianBlur(np.isfinite(v).astype(np.float32), (0, 0), 1.2), 1e-3)
            v[~np.isfinite(fill_gaps(m, 1.5))] = np.nan
            self.v = np.where(land_mask(m.shape), v, np.nan).astype(np.float32)
            self.lut = cmap_lut("magma")
            self.vmin, self.vmax, self.gamma = 1840, 1970, 1.0
            self.title = ("Methane from orbit", "Sentinel-5P TROPOMI, column-average CH₄, May–Oct 2024 (ppb)")
            self.ticks, self.fmt, self.cblabel = [1840, 1880, 1920, 1960], "{:g}", "CH₄ column average (ppb)"
        else:
            m, self.bbox, self.res = s5p("s5p_no2_winter.npz")
            m = np.where(m > 0, m, np.nan)
            self.v = np.log10(fill_gaps(m, 1.5) * 1e6)  # µmol/m²
            self.lut = cmap_lut("inferno")
            self.vmin, self.vmax, self.gamma = 1.0, 2.6, 1.0
            self.title = ("A map of combustion", "Sentinel-5P TROPOMI tropospheric NO₂, Nov 2024 – Feb 2025")
            self.ticks, self.fmt, self.cblabel = [1, 1.5, 2, 2.5], None, "NO₂ column (µmol/m², log scale)"

    def view(self, t):
        if self.p.get("region") == "world":
            z = ease_io(t / self.dur)
            return (-180 + 8 * z, 180 + 8 * z, -90, 90)
        regs = REGIONS[self.key]
        n = len(regs)
        seg = self.dur / n
        i = min(int(t / seg), n - 1)
        u = (t - i * seg) / seg
        world = (-180, 180, -60, 80)
        cur = self._fit(regs[i][1])
        prev = self._fit(regs[i - 1][1]) if i > 0 else world
        k = ease_io(min(u / 0.35, 1))
        return tuple(lerp(a, b, k) for a, b in zip(prev, cur)), regs[i][0], ramp(u, 0.35, 0.12)

    @staticmethod
    def _fit(r):
        lo0, lo1, la0, la1 = r
        cx, cy = (lo0 + lo1) / 2, (la0 + la1) / 2
        w = max(lo1 - lo0, (la1 - la0) * 1.66)
        return (cx - w / 2, cx + w / 2, cy - w / 3.32, cy + w / 3.32)

    def frame(self, t):
        res = self.view(t)
        if self.p.get("region") == "world":
            (lo0, lo1, la0, la1), label, la = res, None, 0
        else:
            (lo0, lo1, la0, la1), label, la = res
        box = (0, 0, W, H)
        # keep aspect: lat span fixed to lon span * H/W
        cy = (la0 + la1) / 2
        span = (lo1 - lo0) * H / W
        fb = FlatBase(lo0, lo1, cy - span / 2, cy + span / 2, box)
        img = fb.render(blank())
        v = fb.sample(self.v, float(self.bbox[0]), float(self.bbox[3]), self.res)
        rgb, ok = colorize(v, self.vmin, self.vmax, self.lut, self.gamma)
        a = 0.88
        img = np.where(ok[..., None], rgb * a + img * (1 - a), img).astype(np.uint8)
        img = fb.coast(img, color=(200, 210, 225), alpha=0.35, thick=1, borders=(lo1 - lo0) < 120)
        im = to_pil(vignette(img, 0.4))
        from PIL import ImageDraw
        ImageDraw.Draw(im, "RGBA").rectangle([0, 0, W, 190], fill=(5, 8, 16, 170))
        heading(im, *self.title, y=95)
        if label:
            draw_text(im, (W / 2, H - 120), label, font(52, "Light"), anchor="ms", alpha=la)
        if self.fmt:
            colorbar(im, 1360, 1000, 440, 16, self.lut, self.vmin, self.vmax, self.cblabel, self.ticks, self.fmt)
        else:
            from PIL import ImageDraw as _d
            colorbar(im, 1360, 1000, 440, 16, self.lut, self.vmin, self.vmax, self.cblabel, [1, 1.5, 2, 2.5], "")
            for tv, s in zip([1, 1.5, 2, 2.5], ["10", "32", "100", "316"]):
                draw_text(im, (1360 + (tv - self.vmin) / (self.vmax - self.vmin) * 440, 1046), s, font(22), fill=MUTED, anchor="ms")
        source_tag(im, "Data: Copernicus Sentinel-5P / TROPOMI Level-2 (ESA), composited for this film")
        return to_np(im)


class Ch4(S5pMap):
    key = "ch4"


class No2(S5pMap):
    key = "no2"


# ───────────────────────────── CO, Canada 2023 ─────────────────────────────
@functools.lru_cache(None)
def co_days():
    d = data.npz("s5p_co_2023_canada.npz")
    daily = d["daily"].astype(np.float32)
    days = [dt.date.fromisoformat(s) for s in d["days"]]
    out = []
    prev = None
    for i in range(len(days)):
        a = daily[i].copy()
        a[(a < 0) | (a > 1)] = np.nan
        a = fill_gaps(a, 2.0)
        if prev is not None:
            a = np.where(np.isfinite(a), a, prev)  # carry forward yesterday where today is missing
        out.append(a)
        prev = a
    return out, days, d["bbox"], float(d["res"])


class CoFire(Scene):
    def __init__(self, sc, dur):
        super().__init__(sc, dur)
        self.days, self.dates, self.bbox, self.res = co_days()
        self.lut = cmap_lut("inferno")
        self.fb = FlatBase(-140, -10, 18, 18 + 130 * H / W, (0, 0, W, H))

    def frame(self, t):
        if self.p.get("stage") == "intro":
            pos = 3.0 * ease_io(t / self.dur)
        else:
            pos = lerp(3.0, len(self.days) - 1.001, min(t / (self.dur * 0.92), 1))
        i = int(pos)
        f = ease_io(pos - i)
        a = self.days[i] if f < 1e-3 else self.days[i] * (1 - f) + self.days[min(i + 1, len(self.days) - 1)] * f
        img = self.fb.render(blank())
        v = self.fb.sample(np.ascontiguousarray(a), float(self.bbox[0]), float(self.bbox[3]), self.res, wrap=False) * 1000  # mmol/m2
        rgb, ok = colorize(v, 22, 70, self.lut, 1.2)
        img = np.where(ok[..., None], rgb * 0.9 + img * 0.1, img).astype(np.uint8)
        img = self.fb.coast(img, color=(200, 210, 225), alpha=0.35, borders=True)
        day = self.dates[min(int(round(pos)), len(self.dates) - 1)]
        x, y = self.fb.xy(-74.0, 40.7)
        if dt.date(2023, 6, 5) <= day <= dt.date(2023, 6, 9):
            img = glow_dot(img, x, y, (120, 220, 255), r=5, halo=16)
        im = to_pil(vignette(img, 0.4))
        from PIL import ImageDraw
        ImageDraw.Draw(im, "RGBA").rectangle([0, 0, W, 190], fill=(5, 8, 16, 170))
        heading(im, "Canada burns, June 2023", "Sentinel-5P TROPOMI carbon monoxide column, one map per day", y=95)
        draw_text(im, (1840, 120), day.strftime("%d %b %Y").upper(), font(60, "Light"), anchor="rs", spacing=3)
        if dt.date(2023, 6, 5) <= day <= dt.date(2023, 6, 9):
            draw_text(im, (x + 18, y + 8), "New York City", font(30, "Medium"), fill=(170, 230, 255), anchor="lm")
        colorbar(im, 1360, 1000, 440, 16, self.lut, 22, 70, "CO column (mmol/m²)", [30, 40, 50, 60, 70])
        source_tag(im, "Data: Copernicus Sentinel-5P / TROPOMI Level-2 (ESA); gaps filled from the previous day")
        return to_np(im)
