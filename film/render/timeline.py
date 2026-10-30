"""Mission timeline of greenhouse-gas observing satellites."""
import numpy as np
from PIL import ImageDraw

from render.base import AMBER, CO2, CYAN, H, INK, MUTED, RED, W, blank, draw_text, ease_out, font, heading, ramp, starfield, to_np, to_pil

# (year, name, agency, status)
MISSIONS = [  # (year, name, agency, status, label level: +up / -down)
    (2009.07, "GOSAT", "JAXA · Japan", "ok", 1),
    (2009.15, "OCO", "NASA", "lost", -1),
    (2014.50, "OCO-2", "NASA", "nasa", 1),
    (2016.97, "TanSat", "China", "ok", -1),
    (2017.78, "Sentinel-5P", "ESA · methane", "ok", 2),
    (2018.83, "GOSAT-2", "JAXA · Japan", "ok", -2),
    (2019.34, "OCO-3", "NASA · on ISS", "nasa", 1),
    (2025.49, "GOSAT-GW", "JAXA · Japan", "ok", -1),
    (2025.56, "MicroCarb", "CNES · France", "ok", 1),
    (2027.50, "CO2M", "ESA/EU · planned", "planned", -2),
]


def draw(scene, t):
    focus = scene.p.get("focus")
    im = to_pil(starfield(t, drift=2, bright=0.5))
    y = 600
    x0, x1 = 160, 1760
    y0, y1 = 2008, 2028.5

    def X(v):
        return x0 + (v - y0) / (y1 - y0) * (x1 - x0)

    d = ImageDraw.Draw(im)
    k = ease_out(t / 1.5)
    d.line([(x0, y), (x0 + (x1 - x0) * k, y)], fill=(80, 92, 115), width=3)
    for yr in range(2008, 2029, 2):
        if X(yr) <= x0 + (x1 - x0) * k:
            d.line([(X(yr), y - 8), (X(yr), y + 8)], fill=(80, 92, 115), width=2)
            draw_text(im, (X(yr), y + 50), str(yr), font(24), fill=MUTED, anchor="ms")
    if focus == "2009":
        heading(im, "Orbiting Carbon Observatory, 2009", "Launch failure: the payload fairing did not separate", y=110)
        items = [m for m in MISSIONS if m[1] in ("OCO", "OCO-2")]
    else:
        heading(im, "A growing fleet", "Satellites dedicated to measuring greenhouse gases from orbit", y=110)
        items = MISSIONS
    n = len(items)
    for i, (yr, name, ag, st, lvl) in enumerate(items):
        a = ramp(t, 1.0 + i * (scene.dur - 3) / max(n, 1), 0.8)
        if a <= 0:
            continue
        up = lvl > 0
        ly = y - 30 - 110 * abs(lvl) if up else y + 60 + 110 * abs(lvl)
        col = {"nasa": CYAN, "lost": RED, "planned": (150, 150, 170), "ok": AMBER}[st]
        d.line([(X(yr), y), (X(yr), ly + (30 if up else -40))], fill=tuple(int(c * a) for c in col), width=2)
        d.ellipse([X(yr) - 9, y - 9, X(yr) + 9, y + 9], fill=tuple(int(c * a) for c in col))
        draw_text(im, (X(yr), ly), name, font(34, "SemiBold"), fill=col, anchor="ms", alpha=a)
        draw_text(im, (X(yr), ly + 34), ag, font(22), fill=MUTED, anchor="ms", alpha=a)
        if st == "lost":
            draw_text(im, (X(yr), ly + (-44 if up else 74)), "✕ lost at launch", font(26, "Medium"), fill=RED, anchor="ms", alpha=a)
    if focus == "2009":
        a = ramp(t, scene.dur * 0.6, 1.0)
        draw_text(im, (W / 2, 900), "24 February 2009 · Taurus XL · Vandenberg — the observatory never reached orbit",
                  font(32), fill=INK, anchor="mm", alpha=a)
    return to_np(im)
