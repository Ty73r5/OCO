"""Control-panel layout and silkscreen artwork.

One layout table drives both the printed graphic (`texture()`) and the 3-D
hardware placed on top of it (`ELEMENTS`, consumed by model.py), so the knobs,
lamps and buttons always land on their legends.

Panel-face coordinates are millimetres measured from the bottom-left corner of
the panel aperture, looking at the panel straight on.

Every legend here is a control that Megger's documentation names for the
DDA-3000/DDA-6000. The arrangement of those controls is an inference — no
panel drawing was reachable.
"""
import functools
import os

from PIL import Image, ImageDraw, ImageFont

from . import params as P

FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")

PW = P.PANEL_X1 - P.PANEL_X0                                   # 1161.0 mm
PH = (P.PANEL_Z1 - P.PANEL_Z0) / __import__("math").cos(__import__("math").radians(P.PANEL_TILT_DEG))
PX = 2.4                                                       # texture pixels per mm

HEADER_H = 60.0
GROUPS = {
    "instr":  (26.0, 22.0, 452.0, PH - HEADER_H - 14.0),
    "dda1":   (468.0, 22.0, 700.0, PH - HEADER_H - 14.0),
    "output": (716.0, 22.0, 1006.0, PH - HEADER_H - 14.0),
    "term":   (1022.0, 22.0, 1135.0, PH - HEADER_H - 14.0),
}
GROUP_TITLE = {
    "instr": "INSTRUMENTATION",
    "dda1": "DDA-1 DIGITAL CONTROL",
    "output": "OUTPUT CONTROL",
    "term": "TERMINALS",
}

# ── elements: (kind, name, x, y, size..., legend) in panel mm ─────────────────
METERS = [
    ("meter_amps", 138.0, 300.0, 186.0, 56.0, "AMMETER", "AMPERES"),
    ("meter_volts", 138.0, 222.0, 186.0, 56.0, "VOLTMETER", "VOLTS"),
    ("meter_timer", 138.0, 144.0, 186.0, 56.0, "TIMER", "CYCLES"),
]
# [DOC] ammeter ranges 200 / 2 000 / 20 000 / 200 000 A, 200 kA default
RANGE_POSITIONS = ["200", "2 000", "20 000", "200 000"]
ROTARIES = [
    ("sel_range", 348.0, 282.0, 36.0, "AMMETER RANGE", RANGE_POSITIONS, 3),
    # [DOC] multi-position OUTPUT SELECTOR, coarse output adjustment
    ("sel_output", 790.0, 202.0, 50.0, "OUTPUT SELECTOR",
     ["1", "2", "3", "4", "5", "6", "7", "8"], 0),
    # [DOC] VERNIER CONTROL, fine adjustment
    ("knob_vernier", 930.0, 202.0, 32.0, "VERNIER CONTROL", None, 0),
]
TOGGLES = [
    # [DOC] ammeter MEM / CONT mode
    ("sw_mode", 348.0, 142.0, "AMMETER MODE", ["MEM", "CONT"]),
    # [DOC] input circuit breaker ON / OFF
    ("sw_breaker", 952.0, 96.0, "CIRCUIT BREAKER", ["ON", "OFF"]),
]
BUTTONS = [
    # [DOC] START energises the output, STOP de-energises it
    ("btn_start", 782.0, 84.0, 28.0, "START", (60, 170, 96)),
    ("btn_stop", 856.0, 84.0, 28.0, "STOP", (196, 54, 46)),
]
# [DOC] panel lamps for operator safety
LAMPS = [
    ("lamp_energized", 745.0, 334.0, "OUTPUT\nENERGIZED", P.C_LAMP_RED),
    ("lamp_thermwarn", 803.0, 334.0, "THERMAL\nWARNING", P.C_LAMP_AMB),
    ("lamp_thermshut", 861.0, 334.0, "THERMAL\nSHUTDOWN", P.C_LAMP_AMB),
    ("lamp_ground", 919.0, 334.0, "GROUND\nINTERLOCK", P.C_LAMP_WHT),
    ("lamp_overrange", 977.0, 334.0, "OVER\nRANGE", P.C_LAMP_RED),
]
LCD = ("lcd", 584.0, 252.0, 186.0, 118.0)           # x, y centre, w, h
KEYPAD = ("keypad", 584.0, 122.0, 186.0, 74.0)
KEYS = ["MENU", "UP", "ENTER", "ESC", "DOWN", "SEL"]
# [DOC] the manual names START terminals (external switch), yellow TIMER STOP
# terminals and VOLTS terminals for the digital voltmeter.
CONNECTORS = []
TERM_X = (1050.0, 1108.0)
TERMINALS = [
    ("term_start", 318.0, "START", (196, 200, 208), "external initiate switch"),
    ("term_timer", 214.0, "TIMER STOP", (226, 178, 36), "timer stop input"),
    ("term_volts", 110.0, "VOLTS", (196, 200, 208), "digital voltmeter input"),
]


@functools.lru_cache(None)
def font(size, weight="Medium", cond=True):
    name = ("BarlowCondensed-" if cond else "Barlow-") + weight + ".ttf"
    p = os.path.join(FONTS, name)
    if not os.path.exists(p):
        p = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, int(size))


def _px(x, y):
    """Panel mm -> texture pixels (texture origin top-left)."""
    return x * PX, (PH - y) * PX


def _text(d, xy, s, size, fill=(236, 240, 246), anchor="mm", weight="Medium", cond=True, spacing=0):
    f = font(size * PX, weight, cond)
    if spacing:
        total = sum(f.getlength(c) + spacing for c in s) - spacing
        x, y = xy
        if anchor[0] == "m":
            x -= total / 2
        elif anchor[0] == "r":
            x -= total
        for c in s:
            d.text((x, y), c, font=f, fill=fill, anchor="l" + anchor[1])
            x += f.getlength(c) + spacing
    else:
        d.multiline_text(xy, s, font=f, fill=fill, anchor=anchor, align="center", spacing=4 * PX)


def texture():
    """Render the panel silkscreen. Returns a PIL image."""
    import math
    W, H = int(PW * PX), int(PH * PX)
    img = Image.new("RGB", (W, H), P.C_PANEL[:3])
    d = ImageDraw.Draw(img)

    # brushed-ish tonal gradient so the panel is not dead flat
    for i in range(H):
        k = 1.0 + 0.10 * (1.0 - i / H)
        d.line([(0, i), (W, i)], fill=tuple(min(255, int(c * k)) for c in P.C_PANEL[:3]))

    hdr_y = _px(0, PH - HEADER_H)[1]
    d.rectangle([0, 0, W, hdr_y], fill=(30, 33, 38))
    d.line([(0, hdr_y), (W, hdr_y)], fill=(96, 102, 112), width=max(2, int(PX)))

    # ── header: brand, model, rating [DOC] ───────────────────────────────────
    _text(d, _px(30, PH - 30), "MEGGER", 27, (242, 245, 250), "lm", "SemiBold", False, spacing=3.2 * PX)
    _text(d, _px(236, PH - 30), "DDA-6000", 27, (226, 178, 36), "lm", "SemiBold", True)
    _text(d, _px(372, PH - 24), "UNIVERSAL CIRCUIT BREAKER TEST SET", 13, (176, 184, 196), "lm")
    _text(d, _px(372, PH - 41), "DIGITAL DATA ACQUISITION  ·  DDA-1 CONTROL SYSTEM", 10, (124, 132, 144), "lm")
    _text(d, _px(PW - 30, PH - 24), "60 000 A", 20, (226, 178, 36), "rm", "SemiBold")
    _text(d, _px(PW - 30, PH - 44), "460 V  1-PHASE INPUT", 10, (124, 132, 144), "rm")

    # ── group frames ─────────────────────────────────────────────────────────
    for key, (x0, y0, x1, y1) in GROUPS.items():
        a, b = _px(x0, y1), _px(x1, y0)
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=5 * PX, outline=(92, 98, 108), width=max(2, int(1.2 * PX)))
        tw = font(11 * PX).getlength(GROUP_TITLE[key]) + 14 * PX
        d.rectangle([a[0] + 14 * PX, a[1] - 7 * PX, a[0] + 14 * PX + tw, a[1] + 7 * PX], fill=(36, 39, 45))
        _text(d, (a[0] + 21 * PX, a[1]), GROUP_TITLE[key], 11, (150, 158, 170), "lm", "SemiBold")

    # ── meters [DOC] 5-digit displays ────────────────────────────────────────
    for name, x, y, w, h, lab, unit in METERS:
        a, b = _px(x - w / 2, y + h / 2), _px(x + w / 2, y - h / 2)
        d.rounded_rectangle([a[0] - 3, a[1] - 3, b[0] + 3, b[1] + 3], radius=3 * PX, fill=(22, 24, 28))
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=2 * PX, fill=(10, 16, 13))
        _text(d, _px(x - w / 2, y + h / 2 + 11), lab, 12, (210, 216, 226), "lm", "SemiBold")
        _text(d, _px(x + w / 2, y + h / 2 + 11), unit, 10, (140, 148, 160), "rm")
        # 5 seven-segment digits, 7 mm numerals [DOC]
        dig = "88888"
        _text(d, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 1 * PX), dig, 26, (36, 92, 58), "mm", "Medium", False, spacing=2 * PX)

    # ── rotary switches ──────────────────────────────────────────────────────
    for name, x, y, r, lab, positions, _dflt in ROTARIES:
        c = _px(x, y)
        d.ellipse([c[0] - r * PX, c[1] - r * PX, c[0] + r * PX, c[1] + r * PX], fill=(38, 41, 47), outline=(96, 102, 112), width=max(2, int(PX)))
        _text(d, _px(x, y - r - 13), lab, 11.5, (206, 212, 222), "mm", "SemiBold")
        if positions:
            n = len(positions)
            span = 250.0 if n > 4 else 150.0
            for i, pos in enumerate(positions):
                ang = math.radians(90 + span / 2 - (span * i / max(n - 1, 1)))
                tx = x + (r + 13) * math.cos(ang)
                ty = y + (r + 13) * math.sin(ang)
                _text(d, _px(tx, ty), pos, 9.5, (196, 202, 212), "mm")
                mx0, my0 = x + (r + 2) * math.cos(ang), y + (r + 2) * math.sin(ang)
                mx1, my1 = x + (r + 6) * math.cos(ang), y + (r + 6) * math.sin(ang)
                d.line([_px(mx0, my0), _px(mx1, my1)], fill=(150, 158, 170), width=max(2, int(PX)))

    # ── toggle switches ──────────────────────────────────────────────────────
    for name, x, y, lab, states in TOGGLES:
        _text(d, _px(x, y + 20), lab, 11.5, (206, 212, 222), "mm", "SemiBold")
        _text(d, _px(x - 26, y), states[0], 10, (186, 192, 202), "rm")
        _text(d, _px(x + 26, y), states[1], 10, (186, 192, 202), "lm")

    # ── push-buttons [DOC] START / STOP ──────────────────────────────────────
    for name, x, y, dia, lab, col in BUTTONS:
        c = _px(x, y)
        rr = dia / 2 * PX
        d.ellipse([c[0] - rr - 4, c[1] - rr - 4, c[0] + rr + 4, c[1] + rr + 4], fill=(30, 33, 38), outline=(100, 106, 116), width=max(2, int(PX)))
        _text(d, _px(x, y - dia / 2 - 12), lab, 12.5, tuple(min(255, int(v * 1.25)) for v in col), "mm", "SemiBold")

    # ── indicator lamps [DOC] ────────────────────────────────────────────────
    for name, x, y, lab, col in LAMPS:
        c = _px(x, y)
        rr = 10.5 * PX
        d.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=(26, 28, 33), outline=(104, 110, 120), width=max(2, int(PX)))
        _text(d, _px(x, y - 20), lab, 9.5, (196, 202, 212), "ma")

    # ── DDA-1 LCD + keypad ───────────────────────────────────────────────────
    _, lx, ly, lw, lh = LCD
    a, b = _px(lx - lw / 2, ly + lh / 2), _px(lx + lw / 2, ly - lh / 2)
    d.rounded_rectangle([a[0] - 4, a[1] - 4, b[0] + 4, b[1] + 4], radius=3 * PX, fill=(22, 24, 28))
    d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=2 * PX, fill=(44, 74, 52))
    _text(d, (a[0] + 8 * PX, a[1] + 14 * PX), "SCR CONTROL", 11, (190, 230, 196), "lm", "Medium")
    _text(d, (a[0] + 8 * PX, a[1] + 34 * PX), "PULSE   6.0 cyc", 11, (190, 230, 196), "lm")
    _text(d, (a[0] + 8 * PX, a[1] + 52 * PX), "ANGLE  142 deg", 11, (190, 230, 196), "lm")
    _text(d, (a[0] + 8 * PX, a[1] + 70 * PX), "RANGE  200 kA", 11, (190, 230, 196), "lm")
    _text(d, (a[0] + 8 * PX, a[1] + 94 * PX), "MEM", 11, (150, 200, 160), "lm")
    _text(d, _px(lx, ly + lh / 2 + 12), "DISPLAY  ·  PROGRAMMING MENUS", 10, (150, 158, 170), "mm")

    _, kx, ky, kw, kh = KEYPAD
    for i, k in enumerate(KEYS):
        cx = kx - kw / 2 + 32 + (i % 3) * 66
        cy = ky + 18 - (i // 3) * 38
        a, b = _px(cx - 27, cy + 14), _px(cx + 27, cy - 14)
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * PX, fill=(52, 56, 64), outline=(96, 102, 112), width=max(1, int(0.8 * PX)))
        _text(d, _px(cx, cy), k, 10, (216, 222, 232), "mm")

    # ── binding-post terminals [DOC] ─────────────────────────────────────────
    for name, y, lab, col, _desc in TERMINALS:
        _text(d, _px((TERM_X[0] + TERM_X[1]) / 2, y + 22), lab, 11, (206, 212, 222), "mm", "SemiBold")
        for tx in TERM_X:
            c = _px(tx, y)
            d.ellipse([c[0] - 13 * PX, c[1] - 13 * PX, c[0] + 13 * PX, c[1] + 13 * PX],
                      fill=(30, 33, 38), outline=(104, 110, 120), width=max(2, int(PX)))
            d.ellipse([c[0] - 8 * PX, c[1] - 8 * PX, c[0] + 8 * PX, c[1] + 8 * PX], fill=col)

    # ── footer warning strip ─────────────────────────────────────────────────
    _text(d, _px(34, 10), "DANGER — HIGH CURRENT.  GROUND INTERLOCK MUST BE CLOSED BEFORE ENERGIZING.",
          10, (214, 170, 60), "lm", "SemiBold")
    _text(d, _px(PW - 34, 10), "DUTY 30 min ON / 30 min OFF", 10, (124, 132, 144), "rm")
    return img


# flat list the 3-D builder consumes: (kind, name, x, y, extra)
def elements():
    out = []
    for name, x, y, w, h, *_ in METERS:
        out.append(("meter", name, x, y, (w, h)))
    for name, x, y, r, lab, positions, dflt in ROTARIES:
        out.append(("rotary", name, x, y, (r, positions, dflt)))
    for name, x, y, lab, states in TOGGLES:
        out.append(("toggle", name, x, y, None))
    for name, x, y, dia, lab, col in BUTTONS:
        out.append(("button", name, x, y, (dia, col)))
    for name, x, y, lab, col in LAMPS:
        out.append(("lamp", name, x, y, col))
    out.append(("lcd", LCD[0], LCD[1], LCD[2], (LCD[3], LCD[4])))
    for name, y, lab, col, _desc in TERMINALS:
        out.append(("terminal", name, (TERM_X[0] + TERM_X[1]) / 2, y, col))
    return out
