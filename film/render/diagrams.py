"""Explanatory diagrams and typographic cards (PIL / OpenCV)."""
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import script
from render import timeline as TL
from render.base import (AMBER, BG, BLUE, CO2, CYAN, DIM, GREEN, H, INK, MUTED, RED, TEAL, VIOLET, W, Scene, blank,
                         draw_text, ease, ease_io, ease_out, fade, font, heading, lerp, ramp, source_tag, starfield,
                         text_size, to_np, to_pil, vignette, wrap)
from render.globe import Globe, glow_dot, orbit_lonlat, soft_glow, stroke

RATE_T_PER_S = 43.184e9 / (365.25 * 86400)  # 2024 total incl. land-use change (GCB via OWID)


def card_bg(t, seed=0):
    return starfield(t + seed, drift=2, bright=0.55)


_BG_CACHE = {}


def dim_earth_bg(t, lon=-30, lat=10, R=900, cx=W * 0.78, cy=H * 0.55, alpha=0.35):
    """Dimmed globe backdrop: rendered once per view, then slowly pushed in (cheap Ken Burns)."""
    key = (lon, lat, R, cx, cy, alpha)
    if key not in _BG_CACHE:
        g = Globe("day")
        g.view(lon, lat, R, cx, cy)
        img = g.render(card_bg(0))
        _BG_CACHE[key] = (img.astype(np.float32) * alpha + np.array(BG, np.float32) * (1 - alpha)).astype(np.uint8)
    base = _BG_CACHE[key]
    s = 1.0 + 0.004 * t
    M = np.float32([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]])
    return cv2.warpAffine(base, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


# ───────────────────────────── cards ─────────────────────────────
class Starfield(Scene):
    def frame(self, t):
        return fade(card_bg(t), ramp(t, 0.5, self.dur - 1.0))


class Title(Scene):
    def frame(self, t):
        from render.goes_scene import interp, disk_geom
        g = interp(34, min(t / self.dur, 0.99))
        cx, cy, r = disk_geom()
        s = (1.25 + 0.08 * t / self.dur) * H / (2 * r)
        M = np.float32([[s, 0, W * 0.5 - cx * s], [0, s, H * 0.95 - cy * s]])
        img = cv2.warpAffine(g, M, (W, H), borderValue=(0, 0, 0))
        img = (img.astype(np.float32) * 0.55).astype(np.uint8)
        img = np.maximum(img, card_bg(t))
        im = to_pil(vignette(img, 0.7))
        a = ramp(t, 0.8, 2.0) * (1 - ramp(t, self.dur - 1.2, 1.2))
        draw_text(im, (W / 2, H * 0.30), script.TITLE, font(112, "ExtraLight"), anchor="mm", alpha=a, spacing=22)
        a2 = ramp(t, 2.2, 1.8) * (1 - ramp(t, self.dur - 1.2, 1.2))
        draw_text(im, (W / 2, H * 0.30 + 92), script.SUBTITLE, font(36, "Light"), fill=(190, 200, 215), anchor="mm", alpha=a2)
        return to_np(im)


class ChapterCard(Scene):
    def frame(self, t):
        title = script.CHAPTERS[self.sc["chapter"]]
        num, name = title.split(" · ")
        im = to_pil(card_bg(t, self.sc["chapter"] * 13))
        a = ramp(t, 0.3, 0.9) * (1 - ramp(t, self.dur - 0.7, 0.7))
        draw_text(im, (W / 2, H / 2 - 70), f"CHAPTER {num}", font(30, "Medium"), fill=CO2, anchor="mm", alpha=a, spacing=10)
        draw_text(im, (W / 2, H / 2 + 10), name, font(80, "ExtraLight"), anchor="mm", alpha=a)
        d = ImageDraw.Draw(im)
        wln = 260 * ease_out((t - 0.3) / 1.2)
        if wln > 1:
            d.line([(W / 2 - wln, H / 2 + 80), (W / 2 + wln, H / 2 + 80)], fill=tuple(int(c * a) for c in DIM), width=2)
        return to_np(im)


class TextCard(Scene):
    def frame(self, t):
        img = dim_earth_bg(t, lon=hash(self.sc["id"]) % 360 - 180)
        im = to_pil(img)
        lines = self.p.get("lines", [])
        n = len(lines)
        step = (self.dur - 2.5) / max(n, 1)
        y0 = H / 2 - (n - 1) * 62
        for i, ln in enumerate(lines):
            a = ramp(t, 0.6 + i * step, 0.9)
            x = 140 + 30 * (1 - ease_out((t - 0.6 - i * step) / 1.0))
            f = font(58 if i == n - 1 else 52, "Light" if i < n - 1 else "Regular")
            draw_text(im, (x, y0 + i * 124), ln, f, fill=INK if i < n - 1 else (255, 214, 160), anchor="lm", alpha=a)
            d = ImageDraw.Draw(im)
            if a > 0:
                d.rectangle([x - 34, y0 + i * 124 - 26, x - 28, y0 + i * 124 + 26], fill=tuple(int(c * a) for c in CO2))
        return to_np(im)


def fmt_int(v):
    return f"{int(v):,}"


class CounterIntro(Scene):
    def frame(self, t):
        im = to_pil(dim_earth_bg(t, lon=10, lat=20, alpha=0.3))
        a = ramp(t, 0.3, 1.0)
        v = RATE_T_PER_S * t
        draw_text(im, (W / 2, H / 2 - 160), "CO₂ RELEASED BY HUMANITY SINCE THIS FILM BEGAN", font(30, "Medium"), fill=MUTED, anchor="mm", alpha=a, spacing=5)
        draw_text(im, (W / 2, H / 2 - 10), fmt_int(v), font(190, "ExtraLight"), anchor="mm", alpha=a)
        draw_text(im, (W / 2, H / 2 + 120), "tonnes", font(44, "Light"), fill=(255, 200, 140), anchor="mm", alpha=a)
        a2 = ramp(t, 4.0, 1.2)
        draw_text(im, (W / 2, H / 2 + 230), "≈ 43.2 billion tonnes per year (2024, fossil + land use)  ·  ≈ 1,370 tonnes per second",
                  font(28), fill=MUTED, anchor="mm", alpha=a2)
        source_tag(im, "Rate: Global Carbon Budget 2024 via Our World in Data (co2_including_luc, World)", a2)
        return to_np(im)


class CounterFinal(Scene):
    def frame(self, t):
        v = RATE_T_PER_S * (getattr(self, "T0", 0.0) - getattr(self, "COUNTER_T0", 0.0) + t)
        im = to_pil(dim_earth_bg(t, lon=-60, lat=0, alpha=0.3))
        a = ramp(t, 0.3, 1.0)
        draw_text(im, (W / 2, H / 2 - 160), "CO₂ RELEASED SINCE THIS FILM BEGAN", font(30, "Medium"), fill=MUTED, anchor="mm", alpha=a, spacing=5)
        draw_text(im, (W / 2, H / 2 - 10), fmt_int(v), font(190, "ExtraLight"), anchor="mm", alpha=a)
        draw_text(im, (W / 2, H / 2 + 120), "tonnes", font(44, "Light"), fill=(255, 200, 140), anchor="mm", alpha=a)
        a2 = ramp(t, 3.0, 1.2)
        trucks = v / 1000.0
        draw_text(im, (W / 2, H / 2 + 230), f"≈ {v / 1e6:.1f} million tonnes in {(v / RATE_T_PER_S) / 60:.0f} minutes",
                  font(30), fill=MUTED, anchor="mm", alpha=a2)
        return to_np(im)


CREDITS = [
    ("h", "THE BREATHING PLANET"),
    ("s", ""),
    ("t", "DATA"),
    ("l", "Atmospheric CO₂, Mauna Loa & global — NOAA Global Monitoring Laboratory; Scripps Institution of Oceanography"),
    ("l", "Earth imagery — NOAA GOES-19 ABI full disk, 23 September 2026 (equinox) (NOAA Open Data on AWS)"),
    ("l", "Sea-surface temperature anomaly — NOAA OISST v2.1 (NOAA Open Data on AWS)"),
    ("l", "Methane, nitrogen dioxide, carbon monoxide — Copernicus Sentinel-5P / TROPOMI (ESA), Level-2 via meeo-s5p on AWS"),
    ("l", "Emissions — Global Carbon Budget, via Our World in Data (owid/co2-data)"),
    ("l", "Global temperature — NASA GISS Surface Temperature Analysis (GISTEMP v4)"),
    ("l", "Base map — Natural Earth"),
    ("s", ""),
    ("t", "SCIENCE REFERENCED"),
    ("l", "Liu et al. (2017), Science — tropical carbon response to the 2015–16 El Niño (OCO-2)"),
    ("l", "Schwandner et al. (2017), Science — urban and volcanic CO₂ from OCO-2"),
    ("l", "Nassar et al. (2017), GRL — power-plant CO₂ from OCO-2"),
    ("l", "Byrne et al. (2023), ESSD — national CO₂ budgets for the global stocktake"),
    ("l", "Byrne et al. (2024), Nature — carbon emissions from the 2023 Canadian wildfires"),
    ("l", "Friedlingstein et al. — Global Carbon Budget 2024"),
    ("s", ""),
    ("t", "NOTES"),
    ("l", "Spectra, footprint and light-path diagrams are illustrative, not measured data."),
    ("l", "OCO mission video from ocov2.jpl.nasa.gov was not accessible from the production environment;"),
    ("l", "all maps and charts here are rendered directly from the public datasets listed above."),
    ("s", ""),
    ("t", "PRODUCTION"),
    ("l", "Narration — synthetic voice (Kokoro, open-weight text-to-speech)"),
    ("l", "Music — generated procedurally for this film"),
    ("l", "Written, visualized and rendered with Claude Code"),
    ("s", ""),
    ("s", ""),
    ("h2", "OCO-2 · launched 2 July 2014 · still watching"),
]


class Credits(Scene):
    def frame(self, t):
        im = to_pil(card_bg(t))
        y = H + 40 - t * (len(CREDITS) * 58 + H * 0.6) / (self.dur - 4)
        y = max(y, H * 0.5 - (len(CREDITS) - 1) * 58 + 40)
        for kind, txt in CREDITS:
            if -80 < y < H + 80 and txt:
                if kind == "h":
                    draw_text(im, (W / 2, y), txt, font(64, "ExtraLight"), anchor="mm", spacing=14)
                elif kind == "h2":
                    draw_text(im, (W / 2, y), txt, font(36, "Light"), fill=CYAN, anchor="mm")
                elif kind == "t":
                    draw_text(im, (W / 2, y), txt, font(26, "Medium"), fill=CO2, anchor="mm", spacing=6)
                else:
                    draw_text(im, (W / 2, y), txt, font(27, "Light"), fill=(205, 212, 225), anchor="mm")
            y += 58 if kind != "h" else 80
        return fade(np.asarray(im).copy(), 1 - ramp(t, self.dur - 2.5, 2.5))


# ───────────────────────────── chapter I ─────────────────────────────
class PpmGrid(Scene):
    """One million cells (1000 x 1000 px); 280 pre-industrial CO2 molecules + 152 added since."""

    def __init__(self, sc, dur):
        super().__init__(sc, dur)
        rng = np.random.default_rng(3)
        self.base = (rng.random((1000, 1000)) ** 2 * 38 + 18).astype(np.uint8)
        idx = rng.choice(1000 * 1000, 432, replace=False)
        self.pts = np.c_[idx % 1000, idx // 1000]

    def frame(self, t):
        img = blank()
        S = 900
        x0, y0 = 120, (H - S) // 2
        cells = cv2.resize(self.base, (S, S), interpolation=cv2.INTER_AREA)
        img[y0:y0 + S, x0:x0 + S] = np.stack([cells * 0.8, cells * 0.9, cells * 1.1], -1).clip(0, 255).astype(np.uint8)
        n1 = int(280 * ease_io((t - 3.0) / 4.0))
        n2 = int(152 * ease_io((t - 9.5) / 3.5))
        layer = np.zeros_like(img)
        for i in range(n1 + n2):
            px, py = self.pts[i]
            c = (235, 240, 250) if i < 280 else CO2
            cv2.circle(layer, (int(x0 + px * S / 1000), int(y0 + py * S / 1000)), 4, c, -1, cv2.LINE_AA)
        glow = soft_glow(layer, 5)
        img = cv2.add(cv2.add(img, layer), glow)
        im = to_pil(img)
        X = x0 + S + 90
        draw_text(im, (X, 260), "1,000,000", font(110, "ExtraLight"), anchor="ls", alpha=ramp(t, 0.3, 1))
        draw_text(im, (X, 310), "molecules of dry air (each pixel = one)", font(30), fill=MUTED, anchor="ls", alpha=ramp(t, 0.3, 1))
        draw_text(im, (X, 470), f"{n1:>3}", font(96, "Light"), fill=(235, 240, 250), anchor="ls", alpha=ramp(t, 3.0, 0.8))
        draw_text(im, (X + 190, 470), "CO₂ before industry", font(34), fill=(235, 240, 250), anchor="ls", alpha=ramp(t, 3.0, 0.8))
        draw_text(im, (X, 620), f"+{n2:>3}", font(96, "Light"), fill=CO2, anchor="ls", alpha=ramp(t, 9.5, 0.8))
        draw_text(im, (X + 190, 620), "added since", font(34), fill=CO2, anchor="ls", alpha=ramp(t, 9.5, 0.8))
        draw_text(im, (X, 800), f"= {n1 + n2} ppm", font(84, "Regular"), anchor="ls", alpha=ramp(t, 13.5, 0.8))
        draw_text(im, (X, 850), "Mauna Loa, May 2026", font(30), fill=MUTED, anchor="ls", alpha=ramp(t, 13.5, 0.8))
        return to_np(im)


STATIONS = [
    ("Mauna Loa", -155.58, 19.54), ("Utqiaġvik (Barrow)", -156.61, 71.32), ("American Samoa", -170.56, -14.25),
    ("South Pole", 0.0, -89.98), ("Cape Grim", 144.69, -40.68), ("Alert", -62.51, 82.45), ("Mace Head", -9.9, 53.33),
    ("Izaña", -16.5, 28.31), ("Mt. Waliguan", 100.9, 36.29), ("Cape Point", 18.49, -34.35), ("Jungfraujoch", 7.98, 46.55),
    ("Ny-Ålesund", 11.89, 78.91), ("Bukit Kototabang", 100.32, -0.2), ("Ushuaia", -68.31, -54.85),
]
GAPS = [("Amazon", -62, -5, 15), ("Congo Basin", 22, 0, 12), ("Siberia", 105, 62, 18), ("Southern Ocean", 80, -55, 20),
        ("Open Pacific", -130, -10, 20), ("Sahel", 5, 15, 12)]


class FlatBase:
    """Equirectangular dark map helper."""

    def __init__(self, lon0=-180, lon1=180, lat0=-90, lat1=90, box=(0, 0, W, H), tex="dark"):
        from render.globe import earth_texture
        self.tex = earth_texture(tex)
        self.set_view(lon0, lon1, lat0, lat1, box)

    def set_view(self, lon0, lon1, lat0, lat1, box=None):
        if box:
            self.box = box
        self.lon0, self.lon1, self.lat0, self.lat1 = lon0, lon1, lat0, lat1

    def xy(self, lon, lat):
        x0, y0, x1, y1 = self.box
        return (x0 + (np.asarray(lon) - self.lon0) / (self.lon1 - self.lon0) * (x1 - x0),
                y0 + (self.lat1 - np.asarray(lat)) / (self.lat1 - self.lat0) * (y1 - y0))

    def grid(self):
        x0, y0, x1, y1 = self.box
        xs = np.arange(x0, x1, dtype=np.float32)
        ys = np.arange(y0, y1, dtype=np.float32)
        lon = self.lon0 + (xs + 0.5 - x0) / (x1 - x0) * (self.lon1 - self.lon0)
        lat = self.lat1 - (ys + 0.5 - y0) / (y1 - y0) * (self.lat1 - self.lat0)
        return np.meshgrid(lon, lat)

    def sample(self, arr, lon_first, lat_first, res, interp=cv2.INTER_LINEAR, wrap=True):
        """Resample a regular lat/lon grid (row 0 = lat_first, descending by res) into the view box."""
        LON, LAT = self.grid()
        if wrap:
            LON = (LON - lon_first) % 360 + lon_first
        mx = ((LON - lon_first) / res - 0.5).astype(np.float32)
        my = ((lat_first - LAT) / res - 0.5).astype(np.float32)
        return cv2.remap(arr, mx, my, interp, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan if arr.dtype == np.float32 else 0)

    def render(self, img):
        th, tw = self.tex.shape[:2]
        x0, y0, x1, y1 = self.box
        reg = self.sample(self.tex, -180, 90, 360 / tw)
        img[y0:y1, x0:x1] = reg
        return img

    def coast(self, img, color=(120, 135, 160), alpha=0.7, thick=1, borders=False):
        from render.globe import border_lines, coast_lines
        pts = []
        for xy in list(coast_lines()) + (list(border_lines()) if borders else []):
            lon, lat = xy[:, 0], xy[:, 1]
            if lon.max() < self.lon0 - 5 or lon.min() > self.lon1 + 5 or lat.max() < self.lat0 - 5 or lat.min() > self.lat1 + 5:
                continue
            px, py = self.xy(lon, lat)
            pts.append(np.round(np.c_[px, py] * 16).astype(np.int32))
        x0, y0, x1, y1 = self.box
        out = stroke(img, pts, color, thick, alpha)
        return out


class Stations(Scene):
    def frame(self, t):
        fb = FlatBase(-180, 180, -80, 85, (60, 150, 1860, 150 + int(1800 * 165 / 360)))
        img = fb.render(blank())
        img = fb.coast(img, alpha=0.45)
        im = to_pil(img)
        heading(im, "A few dots on a big planet", "Selected long-running baseline CO₂ observatories (illustrative, not the full network)",
                alpha=ramp(t, 0.2, 1.0), y=80)
        img = to_np(im)
        for i, (name, lo, la) in enumerate(STATIONS):
            a = ramp(t, 1.0 + i * 0.35, 0.6)
            if a > 0:
                x, y = fb.xy(lo, max(la, -79))
                img = glow_dot(img, x, y, AMBER, r=5, halo=16, alpha=a)
        im = to_pil(img)
        for i, (name, lo, la) in enumerate(STATIONS):
            a = ramp(t, 1.0 + i * 0.35, 0.6) * (1 - ramp(t, 9.5, 1.0))
            x, y = fb.xy(lo, max(la, -79))
            draw_text(im, (x + 12, y - 8), name, font(22, "Medium"), fill=(255, 220, 170), anchor="ls", alpha=a)
        d = ImageDraw.Draw(im, "RGBA")
        for i, (name, lo, la, r) in enumerate(GAPS):
            a = ramp(t, 10.5 + i * 0.8, 1.0)
            if a > 0:
                x, y = fb.xy(lo, la)
                rr = r * 5 * (0.9 + 0.1 * math.sin(t * 2 + i))
                d.ellipse([x - rr, y - rr * 0.8, x + rr, y + rr * 0.8], outline=(110, 170, 255, int(200 * a)), width=3)
                draw_text(im, (x, y), name, font(26, "Medium"), fill=(170, 205, 255), anchor="mm", alpha=a)
        return to_np(im)


# ───────────────────────────── chapter II ─────────────────────────────
class Timeline(Scene):
    def frame(self, t):
        return TL.draw(self, t)


class Launch(Scene):
    """Long-exposure style ascent arc over a dark horizon, with mission event log."""

    EVENTS = [(0.0, "T+0", "Liftoff · Delta II · Vandenberg, California"), (0.25, "", "Fairing separation — this time it opens"),
              (0.55, "", "Second stage burns to orbit"), (0.8, "T+<1 hr", "OCO-2 separates · solar arrays deploy")]

    def frame(self, t):
        img = card_bg(t * 0.3).astype(np.float32)
        yy = np.arange(H, dtype=np.float32)[:, None]
        sky = np.clip((yy - H * 0.35) / (H * 0.65), 0, 1) ** 2
        img += sky[..., None] * np.array([10, 18, 40], np.float32)[None, None]
        img = np.clip(img, 0, 255).astype(np.uint8)
        # ground silhouette
        xs = np.arange(W)
        ridge = (H * 0.86 + 18 * np.sin(xs / 140.0) + 10 * np.sin(xs / 37.0 + 1)).astype(int)
        for x in range(W):
            img[ridge[x]:, x] = (4, 6, 10)
        k = ease_io(min(t / (self.dur * 0.85), 1))
        n = max(int(400 * k), 2)
        s = np.linspace(0, k, n)
        px = W * 0.30 + (s ** 1.6) * W * 0.62
        py = H * 0.84 - np.sin(s * math.pi * 0.5) ** 0.8 * H * 0.72
        pts = [np.round(np.c_[px, py] * 16).astype(np.int32)]
        img = stroke(img, pts, (255, 190, 120), 3, 0.95, glow=0.55)
        img = glow_dot(img, px[-1], py[-1], (255, 200, 140), r=5, halo=30)
        im = to_pil(vignette(img, 0.5))
        draw_text(im, (110, 130), "2 JULY 2014 · 02:56 PDT", font(46, "Light"), anchor="ls", spacing=4, alpha=ramp(t, 0.3, 1))
        draw_text(im, (110, 175), "Vandenberg Air Force Base, California", font(28), fill=MUTED, anchor="ls", alpha=ramp(t, 0.3, 1))
        for i, (f, tag, txt) in enumerate(self.EVENTS):
            a = ramp(t, f * self.dur * 0.85 + 0.5, 0.8)
            y = 300 + i * 64
            draw_text(im, (110, y), "✓" if i else "●", font(30, "SemiBold"), fill=CYAN, anchor="ls", alpha=a)
            draw_text(im, (160, y), txt, font(32, "Regular"), anchor="ls", alpha=a)
        source_tag(im, "Illustration — ascent path not to scale")
        return to_np(im)


class ATrain(Scene):
    SATS = ["OCO-2", "GCOM-W1", "Aqua", "CloudSat", "CALIPSO", "Aura"]

    def frame(self, t):
        g = Globe("day")
        R = 2600
        g.view(-40 + t * 0.8, 20, R, W / 2, H + R - 330)
        img = g.render(card_bg(t), sun=(-30, 10), glow=1.0)
        # satellites on an arc just above the limb
        im = to_pil(img)
        alt = R + 95
        cx, cy = W / 2, H + R - 330
        a = ramp(t, 0.5, 1.0)
        base = -1.70 + 0.004 * t
        pts = []
        for i, name in enumerate(self.SATS):
            ang = base + 0.045 * i
            x, y = cx + alt * math.cos(ang), cy + alt * math.sin(ang)
            pts.append((x, y, name, i))
        arr = to_np(im)
        for x, y, name, i in pts:
            arr = glow_dot(arr, x, y, CYAN if i == 0 else (200, 210, 230), r=6 if i == 0 else 4, halo=20, alpha=a)
        im = to_pil(arr)
        for x, y, name, i in pts:
            draw_text(im, (x, y - 26), name, font(28 if i == 0 else 24, "SemiBold" if i == 0 else "Regular"),
                      fill=CYAN if i == 0 else INK, anchor="ms", alpha=a)
        heading(im, "The A-Train", "Satellites in one line, crossing the same ground minutes apart (circa 2014)", alpha=ramp(t, 0.2, 1))
        source_tag(im, "Illustration — spacing not to scale")
        return to_np(im)


# ───────────────────────────── chapter III ─────────────────────────────
class LightPath(Scene):
    def frame(self, t):
        img = blank()
        top, bot = 250, 880
        # atmosphere band
        yy = np.arange(H, dtype=np.float32)[:, None]
        band = np.clip((yy - top) / (bot - top), 0, 1) ** 1.5 * ((yy >= top) & (yy <= bot))
        img = (img.astype(np.float32) + band[..., None] * np.array([18, 40, 80], np.float32)).astype(np.uint8)
        img[bot:] = (30, 34, 28)
        rng = np.random.default_rng(1)
        mol = np.c_[rng.uniform(0, W, 420), top + (bot - top) * rng.random(420) ** 0.6]
        sun = (230, 120)
        gnd = (960, bot)
        sat = (1650, 150)
        k1 = ease_io((t - 1.0) / 3.5)
        k2 = ease_io((t - 4.5) / 3.5)
        img = stroke(img, [np.round(np.array([sun, (lerp(sun[0], gnd[0], k1), lerp(sun[1], gnd[1], k1))]) * 16).astype(np.int32)],
                     (255, 220, 140), 4, 0.9, glow=0.6) if k1 > 0 else img
        if k2 > 0:
            img = stroke(img, [np.round(np.array([gnd, (lerp(gnd[0], sat[0], k2), lerp(gnd[1], sat[1], k2))]) * 16).astype(np.int32)],
                         (255, 220, 140), 4, 0.9, glow=0.6)
        layer = np.zeros_like(img)
        near = np.zeros(len(mol), bool)
        for (a_, b_, k) in ((sun, gnd, k1), (gnd, sat, k2)):
            if k <= 0:
                continue
            a_, b_ = np.array(a_, float), np.array(b_, float)
            dv = b_ - a_
            u = ((mol - a_) @ dv) / (dv @ dv)
            dd = np.abs(dv[1] * mol[:, 0] - dv[0] * mol[:, 1] + b_[0] * a_[1] - b_[1] * a_[0]) / np.hypot(*dv)
            near |= (u >= 0) & (u <= k) & (dd < 26)
        hot = near & (np.arange(len(mol)) % 3 == 0)
        for (x, y), h_ in zip(mol, hot):
            cv2.circle(layer, (int(x), int(y)), 4 if h_ else 2, CO2 if h_ else (110, 130, 170), -1, cv2.LINE_AA)
        img = cv2.add(img, layer)
        img = cv2.add(img, soft_glow(layer, 4))
        img = glow_dot(img, *sun, (255, 210, 120), r=34, halo=90)
        img = glow_dot(img, *sat, CYAN, r=8, halo=24)
        im = to_pil(img)
        draw_text(im, (sun[0] + 60, sun[1] + 10), "Sunlight", font(34, "Medium"), fill=(255, 220, 150), anchor="ls")
        draw_text(im, (sat[0] - 20, sat[1] - 30), "OCO-2 · 705 km", font(32, "SemiBold"), fill=CYAN, anchor="rs")
        draw_text(im, (gnd[0], bot + 50), "Reflected from the surface", font(30), fill=MUTED, anchor="ms")
        draw_text(im, (60, (top + bot) / 2), "Atmosphere", font(30, "Medium"), fill=(150, 180, 230), anchor="lm")
        a = ramp(t, 8.0, 1.0)
        draw_text(im, (W - 80, bot - 40), "Path through the air: twice", font(36, "Light"), anchor="rs", alpha=a)
        draw_text(im, (W - 80, bot + 50), "Orange: CO₂ molecules absorbing", font(26), fill=CO2, anchor="rs", alpha=ramp(t, 3, 1))
        source_tag(im, "Illustration — not to scale")
        return to_np(im)


def band_model(nu, nu0, B=0.39, T=250.0, even=True, jmax=60, width=0.08):
    """Simple rigid-rotor P/R branch absorption cross-section (arbitrary units), Lorentz lines."""
    sig = np.zeros_like(nu)
    Js = np.arange(0, jmax, 2 if even else 1) + (0 if even else 1)
    for J in Js:
        pop = (2 * J + 1) * math.exp(-1.4388 * B * J * (J + 1) / T)
        for pos in (nu0 + 2 * B * (J + 1), nu0 - 2 * B * J):
            if J == 0 and pos < nu0:
                continue
            sig += pop * width ** 2 / ((nu - pos) ** 2 + width ** 2)
    return sig / sig.max()


BANDS = {
    "o2": dict(name="Oxygen A-band", lam="0.76 µm", nu0=13122.0, B=1.44, even=False, span=(12950, 13180), col=(130, 170, 255), depth=3.0),
    "weak": dict(name="Weak CO₂ band", lam="1.61 µm", nu0=6227.9, B=0.39, even=True, span=(6170, 6280), col=CO2, depth=0.9),
    "strong": dict(name="Strong CO₂ band", lam="2.06 µm", nu0=4853.6, B=0.39, even=True, span=(4805, 4895), col=(255, 110, 80), depth=2.2),
}


class Spectrum(Scene):
    def __init__(self, sc, dur):
        super().__init__(sc, dur)
        self.cache = {}
        for k, b in BANDS.items():
            nu = np.linspace(*b["span"], 1400)
            self.cache[k] = (nu, band_model(nu, b["nu0"], b["B"], even=b["even"]))

    def panel(self, img, box, key, amount, label=True, alpha=1.0):
        b = BANDS[key]
        nu, sig = self.cache[key]
        x0, y0, x1, y1 = box
        tr = np.exp(-b["depth"] * amount * sig)
        xs = np.linspace(x0, x1, len(nu))
        ys = y0 + (1 - tr) * (y1 - y0) * 0.9 + 6
        # rainbow-ish strip of the spectrum with dark absorption lines
        strip_h = 40
        col = np.array(b["col"], np.float32)
        strip = (tr[None, :, None] * col[None, None, :] * np.ones((strip_h, 1, 1))).astype(np.uint8)
        strip = cv2.resize(strip, (x1 - x0, strip_h))
        sy = y1 + 20
        img[sy:sy + strip_h, x0:x1] = (img[sy:sy + strip_h, x0:x1] * (1 - alpha) + strip * alpha).astype(np.uint8)
        pts = [np.round(np.c_[xs, ys] * 16).astype(np.int32)]
        img = stroke(img, pts, b["col"], 2, alpha)
        return img

    def frame(self, t):
        stage = self.p.get("stage")
        img = blank()
        im_text = []
        if stage == "lines":
            amt = 0.25 + 0.75 * ease_io((t - 2.0) / (self.dur - 4.0))
            img = self.panel(img, (160, 260, 1760, 720), "weak", amt)
            im = to_pil(img)
            heading(im, "A barcode written in light", "Sunlight near 1.61 µm after passing through the atmosphere", y=110)
            draw_text(im, (160, 245), "Brightness", font(26), fill=MUTED, anchor="ls")
            draw_text(im, (1760, 860), "wavelength →", font(26), fill=MUTED, anchor="rs")
            draw_text(im, (1760, 245), f"More CO₂ along the path → deeper lines", font(30), fill=CO2, anchor="rs", alpha=ramp(t, 3.0, 1))
            source_tag(im, "Illustrative spectrum (simplified rotational band model), not OCO-2 data")
            return to_np(im)
        keys = ["o2", "weak", "strong"]
        im = None
        for i, k in enumerate(keys):
            a = ramp(t, 0.5 + i * 1.6, 1.0)
            if stage == "ratio" and k != "o2":
                a *= lerp(1.0, 0.3, ramp(t, 1.0, 1.5))
            box = (110 + i * 590, 330, 110 + i * 590 + 520, 640)
            if a > 0:
                img = self.panel(img, box, k, 1.0, alpha=a)
        im = to_pil(img)
        for i, k in enumerate(keys):
            a = ramp(t, 0.5 + i * 1.6, 1.0)
            if stage == "ratio" and k != "o2":
                a *= lerp(1.0, 0.3, ramp(t, 1.0, 1.5))
            b = BANDS[k]
            x = 110 + i * 590
            draw_text(im, (x, 300), b["name"], font(36, "Medium"), fill=b["col"], anchor="ls", alpha=a)
            draw_text(im, (x + 520, 300), b["lam"], font(30, "Light"), anchor="rs", alpha=a)
            draw_text(im, (x, 740), "1,016 spectral channels", font(24), fill=MUTED, anchor="ls", alpha=a)
        if stage == "bands":
            heading(im, "Three spectrometers, one telescope", "Each splits light into ~1,000 colors", y=110)
        else:
            heading(im, "Oxygen is the ruler", "O₂ is a constant 20.95% of dry air", y=110)
            a = ramp(t, 4.0, 1.2)
            draw_text(im, (W / 2, 880), "XCO₂  =  CO₂ molecules in the column  ÷  dry-air molecules in the column (from O₂)",
                      font(40, "Light"), anchor="mm", alpha=a)
            draw_text(im, (W / 2, 950), "Column-averaged dry-air mole fraction, in ppm", font(28), fill=MUTED, anchor="mm", alpha=a)
        source_tag(im, "Illustrative spectra (simplified band models), not OCO-2 data")
        return to_np(im)


class Precision(Scene):
    def frame(self, t):
        img = blank()
        im = to_pil(img)
        heading(im, "One part in four hundred and thirty", "The precision OCO-2 needs for each measurement", y=110)
        d = ImageDraw.Draw(im)
        x0, x1, y = 140, 1780, 520
        # zoom: show 0..430 ppm bar, then zoom into its last 4 ppm
        z = ease_io((t - 3.0) / 4.0)
        lo = lerp(0, 426, z)
        hi = lerp(430, 430, z)
        def X(v):
            return x0 + (v - lo) / (hi - lo) * (x1 - x0)
        d.rectangle([X(max(lo, 0)), y - 40, X(430), y + 40], fill=(40, 60, 90))
        for v in range(int(lo), 431):
            step = 50 if hi - lo > 100 else 1
            if v % step == 0:
                d.line([(X(v), y + 46), (X(v), y + 62)], fill=MUTED, width=2)
                draw_text(im, (X(v), y + 96), f"{v}", font(26), fill=MUTED, anchor="ms")
        a = ramp(t, 6.5, 1.0)
        if a > 0:
            d.rectangle([X(429), y - 40, X(430), y + 40], fill=tuple(int(c * a + 60 * (1 - a)) for c in CO2))
            draw_text(im, ((X(429) + X(430)) / 2, y - 70), "1 ppm", font(44, "Medium"), fill=CO2, anchor="ms", alpha=a)
        draw_text(im, (W / 2, 820), "≈ 0.25% precision", font(64, "Light"), anchor="mm", alpha=ramp(t, 8.0, 1.0))
        draw_text(im, (W / 2, 900), "Like weighing a full suitcase precisely enough to notice one extra sock",
                  font(32), fill=MUTED, anchor="mm", alpha=ramp(t, 10.0, 1.0))
        draw_text(im, (x0, y - 70), "Total column CO₂ (ppm)", font(28), fill=MUTED, anchor="ls", alpha=1 - z)
        return to_np(im)


class Footprints(Scene):
    def __init__(self, sc, dur):
        super().__init__(sc, dur)
        rng = np.random.default_rng(5)
        n = rng.standard_normal((540, 960)).astype(np.float32)
        terr = cv2.GaussianBlur(n, (0, 0), 18) * 3 + cv2.GaussianBlur(n, (0, 0), 4) * 0.8
        terr = (terr - terr.min()) / (terr.max() - terr.min())
        col = np.stack([60 + 70 * terr, 80 + 70 * terr, 45 + 40 * terr], -1)
        self.ground = cv2.resize(col.astype(np.uint8), (W * 2, H * 2))
        cl = cv2.GaussianBlur(rng.standard_normal((270, 480)).astype(np.float32), (0, 0), 6)
        cl = (cl - cl.mean()) / cl.std()
        self.cloud = cv2.resize(np.clip((cl - 0.6) * 1.6, 0, 1), (W * 2, H * 2))

    def frame(self, t):
        pk = 62.0
        slow = 8.0  # time slowed 8x: 3 frames/s become 3/8 per second on screen
        speed = 3.0 * 2.25 * pk / slow  # along-track: one footprint length per frame
        off = int(t * speed) % (H)
        g = self.ground[off:off + H, W // 2:W // 2 + W].astype(np.float32)
        c = self.cloud[off:off + H, W // 2:W // 2 + W][..., None]
        img = (g * (1 - c * 0.9) + 245 * c * 0.9).astype(np.uint8)
        img = (img.astype(np.float32) * 0.8).astype(np.uint8)
        # footprints: 8 across, each 1.29 km x 2.25 km; scale 60 px/km
        pk = 62.0
        fw, fh = 1.29 * pk, 2.25 * pk
        x0 = W / 2 - 4 * fw
        frame_rate = 3.0 / slow
        nframes = int(t * frame_rate) + 1
        layer = img.copy()
        for k in range(nframes):
            yk = H * 0.62 - (nframes - 1 - k) * fh * 0 + (t - k / frame_rate) * speed * 1.0
            yk = H * 0.62 + (t - k / frame_rate) * speed
            if yk > H + fh or yk < -fh:
                continue
            for i in range(8):
                xa = x0 + i * fw
                ci = self.cloud[int(np.clip(off + yk, 0, 2 * H - 1)), int(np.clip(W // 2 + xa + fw / 2, 0, 2 * W - 1))]
                colr = CYAN if ci < 0.3 else (150, 150, 160)
                cv2.rectangle(layer, (int(xa + 2), int(yk - fh / 2 + 2)), (int(xa + fw - 2), int(yk + fh / 2 - 2)), colr, 2, cv2.LINE_AA)
        img = layer
        im = to_pil(img)
        d = ImageDraw.Draw(im, "RGBA")
        d.rectangle([0, 0, W, 200], fill=(5, 8, 16, 200))
        heading(im, "Eight footprints at a time", "Looking straight down from 705 km · ground scrolls as the satellite flies", y=110)
        a = ramp(t, 2.0, 1.0)
        draw_text(im, (W - 80, 300), "≈ 1.3 × 2.25 km each", font(40, "Light"), anchor="rs", alpha=a)
        draw_text(im, (W - 80, 360), "swath ≤ 10.6 km", font(32), fill=MUTED, anchor="rs", alpha=a)
        a = ramp(t, 6.0, 1.0)
        draw_text(im, (W - 80, 470), "3 frames per second", font(40, "Light"), anchor="rs", alpha=a)
        draw_text(im, (W - 80, 530), "= 24 soundings per second", font(32), fill=CYAN, anchor="rs", alpha=a)
        draw_text(im, (80, H - 90), "Cyan: clear view · Gray: cloud in the footprint · time slowed 8×", font(26), fill=INK, anchor="ls")
        source_tag(im, "Illustration — synthetic terrain and clouds; footprint geometry to scale")
        return to_np(im)


class Million(Scene):
    """One simulated day of OCO-2 daylight soundings along the real orbit geometry; clouds thinned (illustrative)."""

    def __init__(self, sc, dur):
        super().__init__(sc, dur)
        self.g = Globe("day")
        hrs = np.linspace(0, 24, 24 * 3600 // 4)  # one sample per 4 s
        lon, lat, alt, T = orbit_lonlat("oco2", hrs, lon_eq=0.0)
        utc = (13.6 - 0.0 / 15 + hrs) % 24
        sub_lon = (12 - utc) * 15
        cosz = np.cos(np.radians(lat)) * np.cos(np.radians(lon - sub_lon))
        day = cosz > 0.05
        self.lon, self.lat, self.hrs = lon[day], lat[day], hrs[day]
        rng = np.random.default_rng(9)
        n = rng.standard_normal((180, 360)).astype(np.float32)
        cm = cv2.GaussianBlur(n, (0, 0), 3)
        cm = (cm - cm.mean()) / cm.std()
        ci = cm[np.clip((90 - self.lat).astype(int), 0, 179), np.clip((self.lon + 180).astype(int), 0, 359)]
        self.clear = ci > 1.15  # ~12% pass (illustrative)

    def frame(self, t):
        self.g.view(20 + t * 1.5, 15, 400)
        img = self.g.render(card_bg(t))
        k = ease_io(min(t / (self.dur * 0.45), 1))
        n = int(k * len(self.lon))
        fade_bad = ramp(t, self.dur * 0.55, 2.0)
        px, py, vis = self.g.project(self.lon[:n], self.lat[:n])
        layer = np.zeros_like(img)
        good = self.clear[:n]
        for sel, colr in ((~good & vis, (150, 200, 255)), (good & vis, CO2)):
            pts = np.c_[px[sel], py[sel]].astype(np.int32)
            if sel is not None and len(pts):
                c = colr if colr == CO2 else tuple(int(v * (1 - 0.85 * fade_bad)) for v in colr)
                for x, y in pts[:: 1]:
                    layer[y - 1:y + 2, x - 1:x + 2] = c
        img = cv2.add(img, layer)
        im = to_pil(img)
        total = int(k * 1_000_000)
        draw_text(im, (110, 200), f"{total:,}", font(96, "ExtraLight"), anchor="ls")
        draw_text(im, (110, 250), "soundings in one day (≈ 24 per second, daylight only)", font(28), fill=MUTED, anchor="ls")
        a = ramp(t, self.dur * 0.55, 1.5)
        draw_text(im, (110, 380), "~100,000", font(80, "Light"), fill=CO2, anchor="ls", alpha=a)
        draw_text(im, (110, 425), "clear enough for the best-quality data", font(28), fill=MUTED, anchor="ls", alpha=a)
        source_tag(im, "Real OCO-2 orbit geometry; sounding density and cloud screening illustrative")
        return to_np(im)


class Retrieval(Scene):
    PARAMS = [("Surface pressure", "hPa", 1013.0, 985.0), ("Temperature offset", "K", 0.0, 1.8), ("Water vapor scale", "×", 1.00, 1.22),
              ("Aerosol optical depth", "", 0.30, 0.08), ("XCO₂", "ppm", 400.0, 428.6)]

    def __init__(self, sc, dur):
        super().__init__(sc, dur)
        self.nu = np.linspace(6170, 6280, 900)
        self.sig = band_model(self.nu, 6227.9)
        rng = np.random.default_rng(2)
        self.noise = rng.standard_normal(len(self.nu)) * 0.012
        self.meas = np.exp(-1.0 * self.sig) * (1 - 0.02 * (self.nu - 6225) / 55) + self.noise

    def frame(self, t):
        k = ease_io((t - 1.5) / (self.dur * 0.6))
        it = int(1 + k * 7)
        amt = lerp(0.55, 1.0, k)
        tilt = lerp(0.0, 0.02, k)
        model = np.exp(-amt * self.sig) * (1 - tilt * (self.nu - 6225) / 55)
        img = blank()
        x0, x1, y0, y1 = 110, 1180, 280, 720
        X = np.linspace(x0, x1, len(self.nu))
        def Y(v):
            return y0 + (1.05 - v) / 0.75 * (y1 - y0)
        img = stroke(img, [np.round(np.c_[X, Y(self.meas)] * 16).astype(np.int32)], (200, 210, 225), 2, 0.9)
        img = stroke(img, [np.round(np.c_[X, Y(model)] * 16).astype(np.int32)], CO2, 2, 0.95)
        res = self.meas - model
        img = stroke(img, [np.round(np.c_[X, 860 - res * 1800] * 16).astype(np.int32)], (130, 170, 255), 2, 0.9)
        im = to_pil(img)
        heading(im, "Fitting the physics", "A radiative-transfer model is adjusted until it matches the measured spectrum", y=110)
        draw_text(im, (x0, y0 - 18), "— measured   ", font(26), fill=(200, 210, 225), anchor="ls")
        draw_text(im, (x0 + 170, y0 - 18), "— model", font(26), fill=CO2, anchor="ls")
        draw_text(im, (x0, 800), "residual (measured − model)", font(24), fill=(130, 170, 255), anchor="ls")
        draw_text(im, (1300, 280), f"ITERATION {it}", font(28, "Medium"), fill=MUTED, anchor="ls", spacing=4)
        for i, (name, unit, v0, v1) in enumerate(self.PARAMS):
            v = lerp(v0, v1, k)
            y = 360 + i * 92
            last = i == len(self.PARAMS) - 1
            draw_text(im, (1300, y), name, font(30, "Medium" if last else "Regular"), fill=CO2 if last else INK, anchor="ls")
            txt = f"{v:,.1f} {unit}" if abs(v) >= 10 else f"{v:.2f} {unit}"
            draw_text(im, (1810, y), txt.strip(), font(30, "Light"), fill=CO2 if last else INK, anchor="rs")
        a = ramp(t, self.dur * 0.75, 1.0)
        draw_text(im, (1300, 860), "Then bias-corrected and checked", font(30), fill=CYAN, anchor="ls", alpha=a)
        draw_text(im, (1300, 900), "against ground-based TCCON stations", font(30), fill=CYAN, anchor="ls", alpha=a)
        source_tag(im, "Illustrative — schematic of the retrieval, values are not real")
        return to_np(im)


class Modes(Scene):
    def frame(self, t):
        img = blank()
        im = to_pil(img)
        heading(im, "Three ways of looking", None, y=110)
        d = ImageDraw.Draw(im)
        panels = [("NADIR", "Straight down over land"), ("GLINT", "Toward the sun's reflection on the ocean"), ("TARGET", "Locked on a ground station as it flies past")]
        for i, (name, sub) in enumerate(panels):
            a = ramp(t, 0.6 + i * (self.dur / 3.6), 1.0)
            cx = 330 + i * 630
            gy = 800
            sx, sy = cx, 330
            colr = tuple(int(c * a) for c in CYAN)
            d.line([(cx - 250, gy), (cx + 250, gy)], fill=tuple(int(c * a) for c in ((90, 120, 80) if i != 1 else (60, 110, 190))), width=6)
            if i == 0:
                d.line([(sx, sy + 20), (sx, gy)], fill=colr, width=3)
            elif i == 1:
                gx = cx + 90
                d.line([(cx - 240, 260), (gx, gy)], fill=tuple(int(c * a) for c in (255, 210, 130)), width=3)
                d.line([(gx, gy), (sx + 150, sy + 10)], fill=colr, width=3)
                sx = sx + 150
                d.ellipse([gx - 30, gy - 8, gx + 30, gy + 8], fill=tuple(int(c * a) for c in (255, 240, 200)))
            else:
                for k, ox in enumerate((-180, -60, 60, 180)):
                    d.line([(cx + ox, sy + 20), (cx, gy - 30)], fill=tuple(int(c * a * (0.4 + 0.15 * k)) for c in CYAN), width=2)
                    d.ellipse([cx + ox - 8, sy - 8, cx + ox + 8, sy + 8], fill=tuple(int(c * a * 0.5) for c in CYAN))
                d.rectangle([cx - 12, gy - 40, cx + 12, gy], fill=tuple(int(c * a) for c in AMBER))
                sx = cx + 180
            d.ellipse([sx - 12, sy - 12, sx + 12, sy + 12], fill=colr)
            draw_text(im, (cx, 900), name, font(40, "Medium"), fill=CYAN, anchor="ms", alpha=a, spacing=6)
            draw_text(im, (cx, 950), sub, font(28), fill=MUTED, anchor="ms", alpha=a)
        source_tag(im, "Illustration — geometry not to scale")
        return to_np(im)


class Sif(Scene):
    def frame(self, t):
        img = blank()
        nu = np.linspace(-1, 1, 900)
        line = 1 - 0.85 * np.exp(-(nu / 0.08) ** 2)
        k = ease_io((t - 4.0) / 5.0)
        sif = 0.12 * k
        obs = (line + sif) / (1 + sif)
        x0, x1, y0, y1 = 140, 1080, 300, 820
        X = np.linspace(x0, x1, len(nu))
        img = stroke(img, [np.round(np.c_[X, y0 + (1.05 - line) * (y1 - y0)] * 16).astype(np.int32)], (120, 130, 150), 2, 0.8)
        img = stroke(img, [np.round(np.c_[X, y0 + (1.05 - obs) * (y1 - y0)] * 16).astype(np.int32)], (255, 90, 90), 3, 0.95)
        # leaf glow
        leaf = np.zeros_like(img)
        cx, cy = 1450, 560
        pts = np.array([[cx - 200, cy + 120], [cx - 60, cy - 160], [cx + 160, cy - 230], [cx + 210, cy - 30], [cx + 40, cy + 170]], np.int32)
        cv2.fillPoly(leaf, [cv2.convexHull(pts)], (40, 150, 60), cv2.LINE_AA)
        cv2.line(leaf, (cx - 200, cy + 120), (cx + 180, cy - 180), (90, 200, 110), 4, cv2.LINE_AA)
        glow = cv2.GaussianBlur(np.where(leaf.sum(-1, keepdims=True) > 0, np.array([255, 40, 40], np.uint8), 0).astype(np.uint8), (0, 0), 30)
        img = cv2.add(img, leaf)
        img = cv2.addWeighted(img, 1, glow, 0.9 * k * (0.75 + 0.25 * math.sin(t * 2)), 0)
        im = to_pil(img)
        heading(im, "Seeing photosynthesis", "Solar-induced fluorescence fills in dark solar lines", y=110)
        draw_text(im, (x0, y1 + 60), "— sunlight alone   ", font(26), fill=(150, 160, 180), anchor="ls")
        draw_text(im, (x0 + 230, y1 + 60), "— sunlight + plant glow", font(26), fill=(255, 110, 110), anchor="ls", alpha=k)
        draw_text(im, ((x0 + x1) / 2, y0 + 0.95 * (y1 - y0) + 40), "Fraunhofer line", font(26), fill=MUTED, anchor="ms")
        draw_text(im, (cx, 880), "Chlorophyll re-emits ~1–2% of absorbed light", font(28), fill=(255, 150, 150), anchor="ms", alpha=k)
        source_tag(im, "Illustration — line shape and glow exaggerated for visibility")
        return to_np(im)


# ───────────────────────────── chapters V–IX ─────────────────────────────
TROPICS = [("South America", -62, -6, "Drought → less photosynthesis", (255, 170, 80)),
           ("Africa", 20, 2, "Heat → more decay and respiration", (255, 110, 90)),
           ("Tropical Asia", 112, -1, "Drought → peat & forest fires", (255, 70, 60))]


class Tropics(Scene):
    def frame(self, t):
        fb = FlatBase(-100, 160, -35, 35, (0, 230, W, 230 + int(W * 70 / 260)))
        img = fb.render(blank())
        img = fb.coast(img, alpha=0.5)
        stage = self.p.get("stage", 0)
        im = to_pil(img)
        if stage == 0:
            heading(im, "2015 vs 2011: the tropics exhale", "OCO-2 results published in Science, October 2017", y=110)
            a = ramp(t, 3.0, 1.2)
            draw_text(im, (W / 2, 840), "+2.5 billion tonnes of carbon", font(84, "Light"), fill=(255, 190, 120), anchor="mm", alpha=a)
            draw_text(im, (W / 2, 920), "released by tropical land during the El Niño year, relative to 2011", font(32), fill=MUTED, anchor="mm", alpha=a)
        else:
            heading(im, "One El Niño, three responses", "Liu et al., Science (2017)", y=110)
        img = to_np(im)
        if stage == 1:
            for i, (name, lo, la, txt, col) in enumerate(TROPICS):
                a = ramp(t, 1.0 + i * (self.dur - 4) / 3, 1.2)
                if a > 0:
                    x, y = fb.xy(lo, la)
                    img = glow_dot(img, x, y, col, r=10, halo=int(70 + 10 * math.sin(t * 2 + i)), alpha=a)
            im = to_pil(img)
            for i, (name, lo, la, txt, col) in enumerate(TROPICS):
                a = ramp(t, 1.0 + i * (self.dur - 4) / 3, 1.2)
                x, y = fb.xy(lo, la)
                draw_text(im, (x, 860), name, font(40, "Medium"), fill=col, anchor="ms", alpha=a)
                draw_text(im, (x, 910), txt, font(28), fill=INK, anchor="ms", alpha=a)
            img = to_np(im)
        im = to_pil(img)
        source_tag(im, "Liu et al. (2017) Science 358, eaam5690 — map markers indicate regions, not measurements")
        return to_np(im)


class LaDome(Scene):
    def frame(self, t):
        img = blank()
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        gnd = 760 + 40 * np.sin(xx / 300.0)
        # mountains ring
        mt = 760 - np.clip(220 - np.abs(xx - 1200) * 0.0, 0, 0)
        img[yy > gnd] = (14, 18, 24)
        ridge_l = 760 - 260 * np.exp(-((xx - 170) / 170) ** 2)
        ridge_r = 760 - 300 * np.exp(-((xx - 1150) / 210) ** 2)
        ridge = np.minimum(ridge_l, ridge_r)
        img[(yy > ridge) & (yy <= gnd)] = (22, 28, 40)
        # city lights
        rng = np.random.default_rng(4)
        for _ in range(500):
            x = rng.uniform(330, 950)
            y = rng.uniform(720, 770)
            img[int(y), int(x)] = (255, 210, 140)
        # dome of CO2
        k = ease_io((t - 1.5) / 4.0)
        dome = np.exp(-(((xx - 640) / 420) ** 2 + ((yy - 760) / 260) ** 2) * 1.6) * (yy < gnd)
        img = np.clip(img + dome[..., None] * np.array([255, 120, 50], np.float32) * 0.55 * k, 0, 255).astype(np.uint8)
        # volcano inset
        a2 = ramp(t, self.dur * 0.45, 1.5)
        vx, vy = 1600, 760
        cone = (yy > vy - 260 + np.abs(xx - vx) * 1.1) & (yy <= gnd)
        img[cone] = (np.array(img[cone], np.float32) * (1 - a2) + np.array([40, 34, 30], np.float32) * a2).astype(np.uint8)
        plume = np.exp(-(((xx - (vx + (vy - 260 - yy) * 0.6)) / (30 + (vy - 260 - yy).clip(0) * 0.4)) ** 2)) * (yy < vy - 250) * np.clip((yy - 150) / 300, 0, 1)
        img = np.clip(img + plume[..., None] * np.array([255, 120, 50], np.float32) * 0.6 * a2, 0, 255).astype(np.uint8)
        im = to_pil(img)
        heading(im, "Cities and volcanoes, seen in CO₂", "OCO-2 results: Schwandner et al., Science (2017)", y=110)
        draw_text(im, (640, 520), "Los Angeles basin", font(40, "Medium"), anchor="ms", alpha=k)
        draw_text(im, (640, 565), "CO₂ dome several ppm above the desert background", font(28), fill=(255, 180, 120), anchor="ms", alpha=k)
        draw_text(im, (vx, 360), "Yasur volcano, Vanuatu", font(34, "Medium"), anchor="ms", alpha=a2)
        draw_text(im, (vx, 400), "volcanic CO₂ plume detected", font(26), fill=(255, 180, 120), anchor="ms", alpha=a2)
        source_tag(im, "Illustration — cross-section not to scale")
        return to_np(im)


class FireTotal(Scene):
    def frame(self, t):
        from render import data
        o = data.owid()
        c = o[(o.year == 2024) & o.iso_code.notna() & ~o.iso_code.astype(str).str.startswith("OWID")].set_index("country").co2.dropna()
        rows = [(n, c[n] / 1000) for n in ["China", "United States", "India", "Russia", "Japan", "Indonesia", "Iran", "Germany", "Canada"]]
        fire = 0.647 * 44 / 12
        rows.insert(3, ("Canada's 2023 wildfires", fire))
        img = blank()
        im = to_pil(img)
        heading(im, "One fire season vs whole nations", "Billion tonnes of CO₂ — wildfire estimate vs 2024 fossil-fuel emissions", y=110)
        d = ImageDraw.Draw(im)
        x0, x1 = 560, 1700
        vmax = 12.5
        for i, (n, v) in enumerate(rows):
            y = 240 + i * 72
            k = ease_out((t - 0.5 - i * 0.35) / 1.0)
            fire_row = "wildfire" in n
            col = (255, 90, 50) if fire_row else (95, 115, 150)
            wbar = (x1 - x0) * v / vmax * max(k, 0)
            d.rectangle([x0, y - 24, x0 + wbar, y + 24], fill=col)
            draw_text(im, (x0 - 20, y), n, font(32, "SemiBold" if fire_row else "Regular"), fill=(255, 170, 120) if fire_row else INK, anchor="rm")
            draw_text(im, (x0 + wbar + 14, y), f"{v:.1f}", font(28), fill=MUTED, anchor="lm", alpha=min(k * 2, 1))
        a = ramp(t, 6.0, 1.0)
        draw_text(im, (W - 100, 980), "≈ 647 million tonnes of carbon (≈ 2.4 billion tonnes CO₂), Byrne et al., Nature (2024)",
                  font(26), fill=(255, 180, 130), anchor="rs", alpha=a)
        source_tag(im, "Fossil: Global Carbon Budget via OWID (2024)")
        return to_np(im)


class Budget(Scene):
    """Global Carbon Budget 2024, 2014–2023 average fluxes (GtC/yr)."""

    SRC = [("Fossil fuels & industry", 9.7, (150, 150, 150)), ("Land-use change", 1.1, (190, 140, 90))]
    SINKS = [("Stays in the atmosphere", 5.2, CO2), ("Absorbed by the ocean", 2.9, (80, 150, 255)), ("Absorbed by land", 3.2, (90, 200, 120))]

    def __init__(self, sc, dur):
        super().__init__(sc, dur)
        self.rng = np.random.default_rng(1)

    def frame(self, t):
        img = blank()
        stage = self.p.get("stage", 0)
        tot = sum(v for _, v, _ in self.SRC)
        sx, sy = 440, 560
        ends = [(1300, 300), (1300, 580), (1300, 860)]
        layer = np.zeros_like(img)
        # flows as streams of particles; width ∝ flux
        for j, ((name, v, col), (ex, ey)) in enumerate(zip(self.SINKS, ends)):
            hl = 1.0 if stage == 0 or stage == j else 0.3
            n = int(v * 60)
            rs = np.random.default_rng(j)
            off = rs.random(n)
            lane = rs.standard_normal(n)
            spd = 0.8 + 0.4 * rs.random(n)
            ph = (t * 0.22 * spd + off) % 1.0
            xs = sx + (ex - sx) * ph
            ys = sy + (ey - sy) * (0.5 - 0.5 * np.cos(np.pi * ph)) + lane * v * 7 * np.sin(np.pi * np.clip(ph * 1.2, 0, 1)) ** 0.7
            c = tuple(int(cc * hl) for cc in col)
            for x, y, p_ in zip(xs, ys, ph):
                cv2.circle(layer, (int(x), int(y)), 3, c, -1, cv2.LINE_AA)
        img = cv2.add(img, layer)
        img = cv2.add(img, soft_glow(layer, 6))
        im = to_pil(img)
        heading(im, "Where our carbon goes", "Global Carbon Budget, average of 2014–2023, billion tonnes of carbon per year", y=110)
        draw_text(im, (sx - 30, sy - 40), f"{tot:.1f}", font(96, "ExtraLight"), anchor="rs")
        draw_text(im, (sx - 30, sy + 10), "emitted per year", font(30), fill=MUTED, anchor="rs")
        draw_text(im, (sx - 30, sy + 60), "9.7 fossil · 1.1 land use", font(26), fill=MUTED, anchor="rs")
        for j, ((name, v, col), (ex, ey)) in enumerate(zip(self.SINKS, ends)):
            hl = 1.0 if stage == 0 or stage == j else 0.35
            a = ramp(t, 1.0 + j * 1.2, 1.0) * hl
            draw_text(im, (ex + 40, ey + 22), f"{v:.1f}", font(76, "Light"), fill=col, anchor="ls", alpha=a)
            draw_text(im, (ex + 190, ey - 6), f"{name}", font(34, "Medium"), anchor="ls", alpha=a)
            draw_text(im, (ex + 190, ey + 34), f"≈ {100 * v / tot:.0f}% of emissions", font(28), fill=MUTED, anchor="ls", alpha=a)
        source_tag(im, "Friedlingstein et al., Global Carbon Budget 2024 (budget imbalance of ≈ −0.4 not shown)")
        return to_np(im)
