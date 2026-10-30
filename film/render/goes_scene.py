"""GOES-19 full-disk day: optical-flow interpolated timelapse over a starfield."""
import functools
import glob
import os

import cv2
import numpy as np

from common_paths import CACHE
from render.base import H, MUTED, Scene, W, draw_text, ease_io, font, starfield, to_np, to_pil, vignette

GDIR = os.path.join(CACHE, "goes")
FLOWDIR = os.path.join(CACHE, "goes_flow")
os.makedirs(FLOWDIR, exist_ok=True)


@functools.lru_cache(None)
def frames_list():
    return sorted(f for f in glob.glob(os.path.join(GDIR, "d266_h*.npy")))


@functools.lru_cache(64)
def load(i):
    fl = frames_list()
    return np.load(fl[i % len(fl)])


def label(i):
    b = os.path.basename(frames_list()[i % len(frames_list())])
    hh, j = int(b[6:8]), int(b[9])
    return hh, 30 * j


def flow(i, j):
    """Flow from frame i to frame j at half resolution (cached on disk)."""
    fl = frames_list()
    p = os.path.join(FLOWDIR, os.path.basename(fl[i])[:-4] + "__" + os.path.basename(fl[j]))
    if os.path.exists(p):
        return np.load(p).astype(np.float32)
    a = cv2.cvtColor(load(i), cv2.COLOR_RGB2GRAY)
    b = cv2.cvtColor(load(j), cv2.COLOR_RGB2GRAY)
    a, b = cv2.resize(a, None, fx=0.5, fy=0.5), cv2.resize(b, None, fx=0.5, fy=0.5)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    f = dis.calc(a, b, None)
    np.save(p, f.astype(np.float16))
    return f


def interp(i, x):
    """Frame at fractional position i + x using bidirectional flow warping."""
    n = len(frames_list())
    i0, i1 = i % n, (i + 1) % n
    A, B = load(i0), load(i1)
    if x < 1e-3:
        return A
    f01 = cv2.resize(flow(i0, i1), (A.shape[1], A.shape[0])) * 2
    f10 = cv2.resize(flow(i1, i0), (A.shape[1], A.shape[0])) * 2
    hh, ww = A.shape[:2]
    gx, gy = np.meshgrid(np.arange(ww, dtype=np.float32), np.arange(hh, dtype=np.float32))
    x = float(x)
    f32 = np.float32
    wa = cv2.remap(A, (gx - f01[..., 0] * f32(x)).astype(f32), (gy - f01[..., 1] * f32(x)).astype(f32), cv2.INTER_LINEAR)
    wb = cv2.remap(B, (gx - f10[..., 0] * f32(1 - x)).astype(f32), (gy - f10[..., 1] * f32(1 - x)).astype(f32), cv2.INTER_LINEAR)
    return cv2.addWeighted(wa, 1 - x, wb, x, 0)


@functools.lru_cache(None)
def disk_geom():
    a = load(len(frames_list()) // 2).max(-1) > 8
    ys, xs = np.nonzero(a)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    r = max(ys.max() - ys.min(), xs.max() - xs.min()) / 2
    return cx, cy, r


class GoesDay(Scene):
    def frame(self, t):
        p = self.p
        pos = p.get("start", 0.0) + p.get("rate", 1.0) * t
        i = int(np.floor(pos))
        x = float(pos - i)
        img = interp(i, x)
        z0, z1 = p.get("zoom", 1.0), p.get("zoom1", p.get("zoom", 1.0))
        z = z0 + (z1 - z0) * ease_io(t / self.dur) + 0.03 * t / max(self.dur, 1)
        cx, cy, r = disk_geom()
        # scale so the disk diameter = 0.94 * H * z
        s = 0.94 * H * z / (2 * r)
        M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
        out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        R = r * s
        yy, xx = np.ogrid[0:H, 0:W]
        rr = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2) / R
        disk = np.clip((1 - rr) * R * 0.5 + 0.5, 0, 1)[..., None]
        bg = starfield(t, drift=2).astype(np.float32)
        out = out.astype(np.float32) * disk + bg * (1 - disk)
        glow = np.where(rr >= 1, np.exp(-(rr - 1) * 30), 0)[..., None] * np.array([90, 150, 255], np.float32) * 0.5
        out = np.clip(out + glow, 0, 255).astype(np.uint8)
        im = to_pil(vignette(out, 0.45))
        hh, mm = label(i if x < 0.5 else i + 1)
        draw_text(im, (W - 70, H - 50), f"GOES-19 · 23 SEP 2026 · {hh:02d}:{mm:02d} UTC", font(24, "Medium"), fill=MUTED, anchor="rs", spacing=2)
        draw_text(im, (70, H - 50), "NOAA GOES-19 ABI full disk · true color by day, infrared by night", font(22), fill=MUTED, anchor="ls")
        return to_np(im)
