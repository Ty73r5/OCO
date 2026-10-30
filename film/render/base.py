"""Shared rendering primitives: canvas, fonts, palette, text, easing, compositing."""
import functools
import math
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common_paths import FONTS

W, H, FPS = 1920, 1080, 24

# Palette
BG = (5, 8, 16)
INK = (236, 240, 247)
MUTED = (140, 152, 172)
DIM = (70, 80, 98)
AMBER = (255, 176, 64)
CO2 = (255, 138, 61)
CYAN = (90, 209, 230)
TEAL = (64, 196, 170)
RED = (235, 84, 72)
BLUE = (86, 148, 240)
GREEN = (120, 205, 120)
VIOLET = (170, 130, 255)


def hexc(c):
    return "#%02x%02x%02x" % c


@functools.lru_cache(None)
def font(size, weight="Regular", cond=False):
    name = ("BarlowCondensed-" if cond else "Barlow-") + weight + ".ttf"
    return ImageFont.truetype(os.path.join(FONTS, name), int(size))


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def lerp(a, b, x):
    return a + (b - a) * x


def ramp(t, t0, dur):
    """0→1 eased between t0 and t0+dur."""
    return ease((t - t0) / max(dur, 1e-6))


def blank(color=BG):
    a = np.empty((H, W, 3), np.uint8)
    a[:] = color
    return a


@functools.lru_cache(None)
def vignette_mask(strength=0.55):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    return (1 - strength * np.clip((r - 0.55) / 0.9, 0, 1) ** 1.6).astype(np.float32)[..., None]


def vignette(img, strength=0.55):
    return (img.astype(np.float32) * vignette_mask(strength)).astype(np.uint8)


@functools.lru_cache(None)
def _stars(seed=7, n=2600):
    rng = np.random.default_rng(seed)
    img = np.zeros((H, W), np.float32)
    xs, ys = rng.integers(0, W, n), rng.integers(0, H, n)
    b = rng.power(6, n)[::-1] * 0.0 + rng.random(n) ** 3
    img[ys, xs] = b
    img = cv2.GaussianBlur(img, (0, 0), 0.6) * 2.2
    big = rng.integers(0, n, 60)
    for i in big:
        cv2.circle(img, (int(xs[i]), int(ys[i])), 1, float(0.6 + 0.4 * b[i]), -1, cv2.LINE_AA)
    return np.clip(img, 0, 1)


def starfield(t=0.0, drift=4.0, bright=0.8):
    s = _stars()
    dx = int(t * drift) % W
    s = np.roll(s, -dx, axis=1)
    base = np.empty((H, W, 3), np.float32)
    base[:] = BG
    tint = np.array([200, 215, 255], np.float32)
    return np.clip(base + s[..., None] * tint * bright, 0, 255).astype(np.uint8)


def to_pil(a):
    return Image.fromarray(a)


def to_np(im):
    return np.asarray(im.convert("RGB"))


def text_size(txt, f):
    l, t, r, b = f.getbbox(txt)
    return r - l, b - t


SUBS = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"}
FALLBACK_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


@functools.lru_cache(None)
def _cmap(path):
    from fontTools.ttLib import TTFont
    return set(TTFont(path).getBestCmap().keys())


@functools.lru_cache(None)
def _font_at(path, size):
    return ImageFont.truetype(path, int(size))


def _runs(txt, f):
    """Split text into (string, font, dy) runs: subscripts and glyphs missing from Barlow get special fonts."""
    have = _cmap(f.path)
    runs = []
    for ch in txt:
        if ch in SUBS:
            r = (SUBS[ch], _font_at(f.path, f.size * 0.62), f.size * 0.12)
        elif ord(ch) not in have and os.path.exists(FALLBACK_FONT):
            r = (ch, _font_at(FALLBACK_FONT, f.size * 0.92), 0.0)
        else:
            r = (ch, f, 0.0)
        if runs and runs[-1][1] is r[1] and runs[-1][2] == r[2]:
            runs[-1] = (runs[-1][0] + r[0], r[1], r[2])
        else:
            runs.append(r)
    return runs


def text_width(txt, f, spacing=0):
    return sum(fr.getlength(s) for s, fr, _ in _runs(txt, f)) + spacing * max(len(txt) - 1, 0)


def draw_text(im, xy, txt, f, fill=INK, anchor="la", alpha=1.0, shadow=True, spacing=0):
    """Draw text on a PIL RGB image with optional soft shadow, alpha, letter spacing and glyph fallback."""
    if alpha <= 0.003 or not txt:
        return
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    col = fill + (int(255 * alpha),)
    x, y = xy
    total = text_width(txt, f, spacing)
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    va = "l" + anchor[1]
    for s_, fr, dy in _runs(txt, f):
        if spacing:
            for c in s_:
                d.text((x, y + dy), c, font=fr, fill=col, anchor=va)
                x += fr.getlength(c) + spacing
        else:
            d.text((x, y + dy), s_, font=fr, fill=col, anchor=va)
            x += fr.getlength(s_)
    bb = layer.getbbox()
    if not bb:
        return
    pad = 18
    bb = (max(bb[0] - pad, 0), max(bb[1] - pad, 0), min(bb[2] + pad, im.size[0]), min(bb[3] + pad, im.size[1]))
    crop = layer.crop(bb)
    if shadow:
        sh = crop.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.85))
        im.paste((0, 0, 0), bb, sh)
    im.paste(crop, bb[:2], crop)


def wrap(txt, f, width):
    words, lines, cur = txt.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if f.getlength(trial) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def blend(a, b, x):
    if x <= 0:
        return a
    if x >= 1:
        return b
    return cv2.addWeighted(a, 1 - x, b, x, 0)


def fade(img, x):
    if x >= 1:
        return img
    return (img.astype(np.float32) * max(x, 0)).astype(np.uint8)


def source_tag(im, txt, alpha=1.0):
    draw_text(im, (60, H - 46), txt, font(22, "Regular"), fill=MUTED, anchor="ls", alpha=0.9 * alpha)


def heading(im, title, sub=None, alpha=1.0, x=110, y=120):
    draw_text(im, (x, y), title, font(54, "Light"), anchor="ls", alpha=alpha)
    if sub:
        draw_text(im, (x, y + 46), sub, font(28, "Regular"), fill=MUTED, anchor="ls", alpha=alpha)


class Scene:
    """Base: subclasses implement frame(t) for 0 <= t < dur and may use self.p (params)."""

    def __init__(self, sc, dur):
        self.sc, self.p, self.dur = sc, sc.get("params", {}), dur

    def frame(self, t):
        raise NotImplementedError


class MplScene(Scene):
    """Scenes drawn with matplotlib; subclasses build the figure in setup() and update in draw(t)."""

    def __init__(self, sc, dur):
        super().__init__(sc, dur)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from render import mplstyle
        mplstyle.apply()
        self.plt = plt
        self.fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
        self.fig.patch.set_facecolor(hexc(BG))
        self.setup()

    def setup(self):
        pass

    def draw(self, t):
        pass

    def overlay(self, im, t):
        pass

    def frame(self, t):
        self.draw(t)
        self.fig.canvas.draw()
        a = np.asarray(self.fig.canvas.buffer_rgba())[..., :3].copy()
        im = to_pil(a)
        self.overlay(im, t)
        return to_np(im)
