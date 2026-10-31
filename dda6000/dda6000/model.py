"""Builds the full DDA-6000 assembly as a list of named, explodable parts."""
import math

import numpy as np
import shapely.geometry as sg
import trimesh

from . import panel, params as P
from .prims import (Assembly, box, cyl, louvers, prism, rod, rrect, shell, stud,
                    textured_plate, tube, union)

TILT = math.radians(P.PANEL_TILT_DEG)
PANEL_CX = (P.PANEL_X0 + P.PANEL_X1) / 2.0
PANEL_CZ = (P.PANEL_Z0 + P.PANEL_Z1) / 2.0
PANEL_CY = P.PANEL_RECESS + (P.PANEL_Z1 - P.PANEL_Z0) * math.tan(TILT) / 2.0
PANEL_N = np.array([0.0, -math.cos(TILT), math.sin(TILT)])      # outward face normal

DENSITY = {           # kg/m^3, for the modelled-mass check
    "steel": 7850, "lam": 7650, "copper": 8960, "alu": 2700,
    "plastic": 1250, "rubber": 1100, "glass": 2500, "pcb": 1900,
}


def panel_pt(u, v, off=0.0):
    """Panel-face coordinates (mm from the aperture's bottom-left) -> model XYZ."""
    pu = u - panel.PW / 2.0
    pv = v - panel.PH / 2.0
    return np.array([
        PANEL_CX + pu,
        PANEL_CY + pv * math.sin(TILT) + PANEL_N[1] * off,
        PANEL_CZ + pv * math.cos(TILT) + PANEL_N[2] * off,
    ])


def panel_part(u, v, depth, radius, off=0.0, sections=28):
    """Cylinder standing proud of the panel face along its normal."""
    a = panel_pt(u, v, off)
    return rod(a, a + PANEL_N * depth, radius, sections=sections)


def _tilt(mesh, center):
    mesh.apply_transform(trimesh.transformations.rotation_matrix(-TILT, (1, 0, 0), center))
    return mesh


# ══════════════════════════════════════════════════════════════════════════════
def build():
    A = Assembly()
    W, D, H = P.W, P.D, P.H
    z0 = P.BASE_Z                      # underside of the cabinet body
    zt = H                             # top of the cabinet
    t = P.SHEET

    # ── 1. base frame and running gear ───────────────────────────────────────
    pz = z0 + P.PLINTH_H / 2
    ring = prism(rrect(W, D, 10).difference(rrect(W - 28, D - 28, 6)), P.PLINTH_H, "z", (W / 2, D / 2, pz))
    cross = [box(56, D - 28, P.PLINTH_H - 12, center=(x, D / 2, pz)) for x in (360.0, 700.0, 1040.0)]
    plinth = union([ring] + cross)
    A.add("plinth", "Base skid / plinth", plinth, P.C_PLINTH, "Structure", stage=4,
          direction=(0, 0, -1), distance=320,
          note="Welded channel skid with three cross members. Carries the transformer and "
               "the caster pads; the low mass concentration here gives the documented low "
               "centre of gravity. [DOC: low centre of gravity]")

    rails = []
    for x in (P.FRAME_TUBE / 2 + 24, W - P.FRAME_TUBE / 2 - 24):
        for y in (P.FRAME_TUBE / 2 + 24, D - P.FRAME_TUBE / 2 - 24):
            rails.append(box(P.FRAME_TUBE, P.FRAME_TUBE, P.BODY_H - P.PLINTH_H,
                             center=(x, y, z0 + P.PLINTH_H + (P.BODY_H - P.PLINTH_H) / 2)))
    for y in (P.FRAME_TUBE / 2 + 24, D - P.FRAME_TUBE / 2 - 24):
        rails.append(box(W - 48, P.FRAME_TUBE, P.FRAME_TUBE, center=(W / 2, y, zt - P.FRAME_TUBE / 2 - 6)))
    for x in (P.FRAME_TUBE / 2 + 24, W - P.FRAME_TUBE / 2 - 24):
        rails.append(box(P.FRAME_TUBE, D - 48, P.FRAME_TUBE, center=(x, D / 2, zt - P.FRAME_TUBE / 2 - 6)))
    A.add("frame", "Internal frame", union(rails), P.C_CABINET_DK, "Structure", stage=4,
          direction=(0, 0, 1), distance=620,
          note="Corner posts and top rails the skins bolt to. [INF]")

    # casters: all four swivel and lock [DOC]
    for sx, sy, tag, lab in ((1, 1, "fl", "front-left"), (-1, 1, "fr", "front-right"),
                             (1, -1, "rl", "rear-left"), (-1, -1, "rr", "rear-right")):
        cx = P.CASTER_INSET_X if sx > 0 else W - P.CASTER_INSET_X
        cy = P.CASTER_INSET_Y if sy > 0 else D - P.CASTER_INSET_Y
        wheel_y = cy + (P.CASTER_OFFSET if sy > 0 else -P.CASTER_OFFSET)
        wz = P.CASTER_WHEEL_DIA / 2
        parts = [
            cyl(P.CASTER_WHEEL_DIA / 2 - 15, P.CASTER_WHEEL_W, "x", (cx, wheel_y, wz), sections=40),
            box(P.CASTER_PLATE, P.CASTER_PLATE, 10, center=(cx, cy, z0 - 5), r=10),
            box(26, P.CASTER_WHEEL_W + 34, 96, center=(cx - P.CASTER_WHEEL_W / 2 - 13, wheel_y, wz + 26)),
            box(26, P.CASTER_WHEEL_W + 34, 96, center=(cx + P.CASTER_WHEEL_W / 2 + 13, wheel_y, wz + 26)),
            box(P.CASTER_WHEEL_W + 60, P.CASTER_WHEEL_W + 34, 16, center=(cx, wheel_y, wz + 66)),
            cyl(26, 34, "z", (cx, cy, z0 - 24), sections=20),
            box(54, 16, 30, center=(cx, wheel_y - (34 if sy > 0 else -34), 28)),   # brake pedal
        ]
        A.add(f"caster_{tag}", f"Swivel caster, {lab}", union(parts), P.C_ZINC, "Running gear",
              stage=4, direction=(0, 0, -1), distance=260,
              note="6 in locking swivel caster. All four swivel and all four lock. [DOC]")
        A.add(f"tyre_{tag}", f"Caster tyre, {lab}",
              tube(P.CASTER_WHEEL_DIA / 2, P.CASTER_WHEEL_DIA / 2 - 16, P.CASTER_WHEEL_W + 2,
                   "x", (cx, wheel_y, wz), sections=40),
              P.C_RUBBER, "Running gear", stage=4, direction=(0, 0, -1), distance=260,
              note="Solid tread.", metal=0.0, rough=0.9)

    # tow ring [DOC]
    ring = tube(58, 34, 20, "y", (W / 2, -16, z0 + 34), sections=32)
    ring = union([ring,
                  box(60, 62, 34, center=(W / 2, 18, z0 + 34)),
                  box(150, 14, 70, center=(W / 2, 48, z0 + 40))])
    A.add("tow_ring", "Tow ring", ring, P.C_ZINC, "Running gear", stage=4,
          direction=(0, -1, 0), distance=300,
          note="Front tow eye for moving the set by hand or by vehicle. [DOC]")

    # lifting eyes [DOC]
    eyes = []
    for x in (170, W - 170):
        for y in (150, D - 150):
            eyes.append(union([
                tube(38, 21, 16, "x", (x, y, zt + 44), sections=28),
                box(16, 54, 50, center=(x, y, zt + 16)),
                box(96, 96, 10, center=(x, y, zt - 2), r=12),
            ]))
    A.add("lift_eyes", "Lifting eyes (4)", union(eyes), P.C_ZINC, "Running gear", stage=1,
          direction=(0, 0, 1), distance=300,
          note="Four lifting eyes for crane handling. [DOC]")

    # ── 2. enclosure skins ───────────────────────────────────────────────────
    body_z = z0 + P.PLINTH_H
    body_h = zt - body_z

    for sx, tag, lab in ((0, "left", "Left"), (1, "right", "Right")):
        x = t / 2 if sx == 0 else W - t / 2
        skin = box(t, D - 2 * t, body_h, center=(x, D / 2, body_z + body_h / 2))
        A.add(f"skin_{tag}", f"{lab} side skin", skin, P.C_CABINET, "Enclosure", stage=1,
              direction=(-1 if sx == 0 else 1, 0, 0), distance=620,
              note="Removable sheet-metal side panel. [DOC: sheet-metal enclosure]")

    back = box(W, t, body_h, center=(W / 2, D - t / 2, body_z + body_h / 2))
    A.add("skin_back", "Rear skin", back, P.C_CABINET, "Enclosure", stage=1,
          direction=(0, 1, 0), distance=620, note="Rear access panel.")

    grille_rows = []
    for zz in np.arange(body_z + 120, zt - 180, 26):
        grille_rows.append(box(560, 6, 14, center=(W / 2, D - t - 3, zz)))
    A.add("rear_grille", "Rear exhaust grille", union(grille_rows), P.C_BLACK, "Enclosure",
          stage=1, direction=(0, 1, 0), distance=700, note="Cooling-air exhaust. [INF]")

    top = box(W, D, t, center=(W / 2, D / 2, zt - t / 2), r=P.CORNER_R, r_axis="z")
    A.add("skin_top", "Top cover", top, P.C_CABINET, "Enclosure", stage=1,
          direction=(0, 0, 1), distance=720, note="Bolted top cover.")

    # front skin: aperture for the control panel, cut-outs for vents and output bay
    face = rrect(W, body_h, P.CORNER_R, W / 2, body_z + body_h / 2)
    face = face.difference(sg.box(P.PANEL_X0, P.PANEL_Z0, P.PANEL_X1, P.PANEL_Z1))
    face = face.difference(sg.box(P.VENT_X0, P.VENT_Z0, P.VENT_X1, P.VENT_Z1))
    face = face.difference(sg.box(P.OUTPUT_BAY_X0, P.OUTPUT_BAY_Z0, P.OUTPUT_BAY_X1, P.OUTPUT_BAY_Z1))
    front = prism(face, t, "y", (0, t / 2, 0))
    A.add("skin_front", "Front skin", front, P.C_CABINET, "Enclosure", stage=1,
          direction=(0, -1, 0), distance=640,
          note="Front panel with the control-panel aperture, vent bank and output bay.")

    A.add("louver_bank", "Front louver bank",
          louvers(P.VENT_X0 + 10, P.VENT_X1 - 10, P.VENT_Z0 + 8, P.VENT_Z1 - 8, t, 26,
                  P.LOUVER_H, P.LOUVER_GAP),
          P.C_CABINET_DK, "Enclosure", stage=1, direction=(0, -1, 0), distance=720,
          note="Stamped intake louvers. [INF]")

    # recess walls around the control panel
    ap_w, ap_h = P.PANEL_X1 - P.PANEL_X0, P.PANEL_Z1 - P.PANEL_Z0
    recess = []
    depth_bot, depth_top = P.PANEL_RECESS, P.PANEL_RECESS + ap_h * math.tan(TILT)
    recess.append(box(ap_w, depth_top, t, center=(PANEL_CX, depth_top / 2, P.PANEL_Z1 - t / 2)))
    recess.append(box(ap_w, depth_bot, t, center=(PANEL_CX, depth_bot / 2, P.PANEL_Z0 + t / 2)))
    for x in (P.PANEL_X0 + t / 2, P.PANEL_X1 - t / 2):
        side = sg.Polygon([(0, P.PANEL_Z0), (depth_bot, P.PANEL_Z0),
                           (depth_top, P.PANEL_Z1), (0, P.PANEL_Z1)])
        recess.append(prism(side, t, "x", (x, 0, 0)))
    A.add("panel_recess", "Panel recess shroud", union(recess), P.C_CABINET_DK, "Control panel",
          stage=2, direction=(0, -1, 0), distance=420,
          note="Formed shroud that sets the panel back and tips it toward the operator. [INF]")

    # ── 3. control panel ─────────────────────────────────────────────────────
    tex = panel.texture()
    plate = textured_plate(panel.PW, panel.PH, P.PANEL_THK, tex)
    plate.apply_translation((PANEL_CX, PANEL_CY, PANEL_CZ))
    _tilt(plate, (PANEL_CX, PANEL_CY, PANEL_CZ))
    A.add("panel_plate", "Control panel faceplate", plate, (255, 255, 255, 255), "Control panel",
          stage=2, direction=tuple(PANEL_N), distance=520,
          note="Silkscreened panel carrying every control Megger documents for this set. [DOC]",
          metal=0.15, rough=0.55)

    sub = shell(panel.PW - 40, 150, panel.PH - 40, 2.0, (0, 0, 0), faces="newtb")
    sub.apply_translation((PANEL_CX, PANEL_CY + 78, PANEL_CZ))
    _tilt(sub, (PANEL_CX, PANEL_CY, PANEL_CZ))
    A.add("panel_subchassis", "Panel sub-chassis", sub, P.C_CABINET_DK, "Control panel",
          stage=3, direction=tuple(PANEL_N), distance=330,
          note="Box behind the faceplate holding the meters, DDA-1 module and switch gear. [INF]")

    for kind, name, u, v, extra in panel.elements():
        if kind == "meter":
            w, h = extra
            bez = box(w + 10, 14, h + 10, center=(0, 0, 0), r=4, r_axis="y")
            bez.apply_translation(panel_pt(u, v, 5))
            _tilt(bez, panel_pt(u, v, 5))
            lens = box(w, 4, h, center=(0, 0, 0))
            lens.apply_translation(panel_pt(u, v, 11))
            _tilt(lens, panel_pt(u, v, 11))
            A.add(name, {"meter_amps": "Ammeter", "meter_volts": "Voltmeter",
                         "meter_timer": "Timer"}[name] + " display",
                  union([bez, lens]), P.C_BLACK, "Control panel", stage=2,
                  direction=tuple(PANEL_N), distance=660,
                  note="5-digit display, 0.281 in (7 mm) numerals. [DOC]", metal=0.1, rough=0.3)
        elif kind == "rotary":
            r, positions, _d = extra
            knob = union([
                panel_part(u, v, 30, r * 0.56, off=2, sections=36),
                panel_part(u, v, 9, r * 0.70, off=2, sections=36),
                rod(panel_pt(u, v + r * 0.30, 18), panel_pt(u, v + r * 0.30, 33), 3.4, sections=12),
            ])
            lab = {"sel_range": "AMMETER RANGE selector",
                   "sel_output": "OUTPUT SELECTOR (coarse)",
                   "knob_vernier": "VERNIER CONTROL (fine)"}[name]
            A.add(name, lab, knob, P.C_BLACK, "Control panel", stage=2,
                  direction=tuple(PANEL_N), distance=680,
                  note=("Ranges 200 / 2 000 / 20 000 / 200 000 A, 200 kA default. [DOC]"
                        if name == "sel_range" else
                        "Multi-position coarse output adjustment. [DOC]" if name == "sel_output"
                        else "Fine output adjustment. [DOC]"), metal=0.2, rough=0.5)
        elif kind == "toggle":
            body = panel_part(u, v, 13, 9.5, off=1, sections=20)
            lev = rod(panel_pt(u, v, 12), panel_pt(u + 9, v + 7, 26), 3.0, sections=12)
            tip = rod(panel_pt(u + 8, v + 6, 24), panel_pt(u + 10, v + 8, 30), 5.2, sections=14)
            lab = "AMMETER MODE MEM/CONT" if name == "sw_mode" else "CIRCUIT BREAKER ON/OFF"
            A.add(name, lab, union([body, lev, tip]), P.C_ZINC, "Control panel", stage=2,
                  direction=tuple(PANEL_N), distance=700, note="[DOC]")
        elif kind == "button":
            dia, col = extra
            ring = panel_part(u, v, 7, dia / 2 + 4, off=1, sections=32)
            cap = panel_part(u, v, 9, dia / 2, off=6, sections=32)
            A.add(name + "_bezel", ("START" if name == "btn_start" else "STOP") + " bezel",
                  ring, P.C_ZINC, "Control panel", stage=2, direction=tuple(PANEL_N), distance=660)
            A.add(name, ("START" if name == "btn_start" else "STOP") + " push-button",
                  cap, tuple(col) + (255,), "Control panel", stage=2,
                  direction=tuple(PANEL_N), distance=730,
                  note=("Energises the output. [DOC]" if name == "btn_start"
                        else "De-energises the output. [DOC]"), metal=0.05, rough=0.4)
        elif kind == "lamp":
            bez = panel_part(u, v, 8, 11.5, off=1, sections=28)
            dome = trimesh.creation.icosphere(subdivisions=2, radius=9.0)
            dome.apply_translation(panel_pt(u, v, 9))
            A.add(name + "_bezel", "Lamp bezel", bez, P.C_ZINC, "Control panel", stage=2,
                  direction=tuple(PANEL_N), distance=660)
            A.add(name, {"lamp_energized": "OUTPUT ENERGIZED lamp",
                         "lamp_thermwarn": "THERMAL WARNING lamp",
                         "lamp_thermshut": "THERMAL SHUTDOWN lamp",
                         "lamp_ground": "GROUND INTERLOCK lamp",
                         "lamp_overrange": "OVER RANGE lamp"}[name],
                  dome, tuple(extra), "Control panel", stage=2,
                  direction=tuple(PANEL_N), distance=730,
                  note="Operator-safety indicator. [DOC]", metal=0.0, rough=0.25)
        elif kind == "lcd":
            w, h = extra
            bez = box(w + 12, 12, h + 12, center=(0, 0, 0), r=4, r_axis="y")
            bez.apply_translation(panel_pt(u, v, 4))
            _tilt(bez, panel_pt(u, v, 4))
            glass = box(w, 4, h, center=(0, 0, 0))
            glass.apply_translation(panel_pt(u, v, 10))
            _tilt(glass, panel_pt(u, v, 10))
            A.add("lcd", "DDA-1 LCD display", union([bez, glass]), P.C_BLACK, "Control panel",
                  stage=2, direction=tuple(PANEL_N), distance=660,
                  note="Menu display for the DDA-1 digital control system. [DOC]",
                  metal=0.1, rough=0.25)
        elif kind == "terminal":
            posts = []
            for tx in panel.TERM_X:
                posts.append(panel_part(tx, v, 5, 13.5, off=1, sections=24))     # insulating base
                posts.append(panel_part(tx, v, 17, 7.0, off=5, sections=6))      # knurled nut
                posts.append(panel_part(tx, v, 9, 4.0, off=20, sections=16))     # post
            lab, desc = {t[0]: (t[2], t[4]) for t in panel.TERMINALS}[name]
            A.add(name, lab + " terminals", union(posts), tuple(extra) + (255,), "Control panel",
                  stage=2, direction=tuple(PANEL_N), distance=700,
                  note=f"Binding-post pair, {desc}. [DOC]", metal=0.55, rough=0.4)

    keys = []
    for i, _k in enumerate(panel.KEYS):
        kx = panel.KEYPAD[1] - panel.KEYPAD[3] / 2 + 32 + (i % 3) * 66
        ky = panel.KEYPAD[2] + 18 - (i // 3) * 38
        cap = box(50, 7, 26, center=(0, 0, 0), r=3, r_axis="y")
        cap.apply_translation(panel_pt(kx, ky, 4))
        _tilt(cap, panel_pt(kx, ky, 4))
        keys.append(cap)
    A.add("keypad", "DDA-1 keypad", union(keys), (74, 79, 88, 255), "Control panel", stage=2,
          direction=tuple(PANEL_N), distance=620, note="Menu navigation keys. [INF]")

    # ── 4. main transformer ──────────────────────────────────────────────────
    cx, cy, cz = P.XFMR_X, P.XFMR_Y, P.XFMR_Z
    win_w = (P.CORE_W - 2 * P.CORE_LEG - P.CORE_CENTRE_LEG) / 2.0
    win_h = P.CORE_H - 2 * P.CORE_YOKE
    prof = sg.box(-P.CORE_W / 2, -P.CORE_H / 2, P.CORE_W / 2, P.CORE_H / 2)
    for s in (-1, 1):
        wx = s * (P.CORE_CENTRE_LEG / 2 + win_w / 2)
        prof = prof.difference(sg.box(wx - win_w / 2, -win_h / 2, wx + win_w / 2, win_h / 2))
    n_pack = max(int(round(P.CORE_STACK / P.LAM_PITCH)), 1)
    pack_t = P.CORE_STACK / n_pack - 1.1                  # 1.1 mm gap reads as laminations
    packs = []
    for i in range(n_pack):
        yy = cy - P.CORE_STACK / 2 + (i + 0.5) * P.CORE_STACK / n_pack
        packs.append(prism(prof, pack_t, "y", (cx, yy, cz)))
    A.add("core", "Transformer core", union(packs), P.C_STEEL_LAM, "Power train",
          stage=4, direction=(0, 0, -1), distance=0,
          note="Shell-form grain-oriented silicon-steel stack, centre leg wound. "
               "Geometry inferred; sized against the documented 545 kg. [INF]",
          metal=0.9, rough=0.55)

    clamps = []
    for s in (-1, 1):
        clamps.append(box(P.CORE_W + 30, P.CORE_STACK + 40, 14,
                          center=(cx, cy, cz + s * (P.CORE_H / 2 + 7)), r=6, r_axis="z"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            clamps.append(rod((cx + sx * (P.CORE_W / 2 + 10), cy + sy * (P.CORE_STACK / 2 + 14), cz - P.CORE_H / 2 - 14),
                              (cx + sx * (P.CORE_W / 2 + 10), cy + sy * (P.CORE_STACK / 2 + 14), cz + P.CORE_H / 2 + 14),
                              8, sections=14))
    A.add("core_clamps", "Core clamping frame", union(clamps), P.C_CABINET_DK, "Power train",
          stage=4, direction=(0, 0, 1), distance=430, note="Channel clamps and tie rods. [INF]")

    def winding(inner_w, inner_d, build, h, color, name, label, note, stage, dist):
        ow, od = inner_w + 2 * build, inner_d + 2 * build
        ring = rrect(ow, od, 14).difference(rrect(inner_w, inner_d, 10))
        m = prism(ring, h, "z", (cx, cy, cz))
        A.add(name, label, m, color, "Power train", stage=stage,
              direction=(0, 0, 1), distance=dist, note=note, metal=0.8, rough=0.45)
        return ow, od

    pw_i, pd_i = P.CORE_CENTRE_LEG + 2 * P.COIL_CLEAR, P.CORE_STACK + 2 * P.COIL_CLEAR
    pw_o, pd_o = winding(pw_i, pd_i, P.COIL_PRI_T, P.COIL_H, P.C_WIRE,
                         "coil_primary", "Primary winding",
                         "460 V single-phase primary on the centre leg. [DOC: 460 V input]",
                         4, 560)
    sw_i, sd_i = pw_o + 16, pd_o + 16
    sw_o, sd_o = winding(sw_i, sd_i, P.COIL_SEC_T, P.COIL_H, P.C_COPPER,
                         "coil_secondary", "Secondary winding",
                         "Few-turn heavy copper secondary — the 60 000 A output winding. [DOC: 60 kA]",
                         4, 760)
    ins = prism(rrect(sw_i - 2, sd_i - 2, 12).difference(rrect(pw_o + 2, pd_o + 2, 12)),
                P.COIL_H + 16, "z", (cx, cy, cz))
    A.add("coil_insulation", "Inter-winding insulation", ins, P.C_INSUL, "Power train",
          stage=4, direction=(0, 0, 1), distance=660, note="Barrier between primary and secondary.",
          metal=0.0, rough=0.8)

    # ── 5. output bus, CT and terminals ──────────────────────────────────────
    bay_cx = (P.OUTPUT_BAY_X0 + P.OUTPUT_BAY_X1) / 2.0
    pad_x = (bay_cx - P.BUS_PITCH / 2, bay_cx + P.BUS_PITCH / 2)
    sec_top = cz + P.COIL_H / 2
    bus_y = 150.0
    for i, px in enumerate(pad_x):
        tag = "a" if i == 0 else "b"
        sx = cx + (-1 if i == 0 else 1) * (sw_o / 2 - 30)
        seg = union([
            box(60, 40, P.BUS_T, center=(sx, cy, sec_top + 24), r=8, r_axis="z"),
            box(P.BUS_T, 40, 150, center=(sx, cy, sec_top + 100)),
            box(abs(px - sx) + P.BUS_T, 40, P.BUS_T, center=((sx + px) / 2, cy, sec_top + 168)),
            box(P.BUS_T, abs(cy - bus_y), 40, center=(px, (cy + bus_y) / 2, sec_top + 168)),
            box(P.BUS_T, 40, abs(sec_top + 168 - P.BUS_Z), center=(px, bus_y, (sec_top + 168 + P.BUS_Z) / 2)),
        ])
        A.add(f"bus_{tag}", f"Output bus bar {tag.upper()}", seg, P.C_COPPER, "Output", stage=3,
              direction=(0, -0.55, 1), distance=560,
              note="Heavy copper run from the secondary to the front output pad. [INF]",
              metal=0.95, rough=0.35)

        pad = box(P.BUS_W, bus_y + 30, P.BUS_T, center=(px, bus_y / 2 + 6, P.BUS_Z), r=10, r_axis="z")
        s_list = []
        for dx in (-54, -18, 18, 54):
            s_list.append(stud((px + dx, -P.STUD_LEN / 2 + 8, P.BUS_Z), "y",
                               P.STUD_DIA, P.STUD_LEN, head=True))
        A.add(f"pad_{tag}", f"Output terminal pad {tag.upper()}", union([pad] + s_list),
              P.C_COPPER_DK, "Output", stage=3, direction=(0, -1, 0), distance=680,
              note="Studded pad. Leads bolt here, or the stab adapter board mounts to it. [DOC]",
              metal=0.95, rough=0.4)

    A.add("ct_output", "Output current transformer",
          union([tube(P.CT_OD / 2, P.CT_ID / 2, P.CT_W, "z", (pad_x[0], bus_y + 90, P.BUS_Z + 210), sections=40),
                 box(70, 46, 34, center=(pad_x[0] + P.CT_OD / 2 + 20, bus_y + 90, P.BUS_Z + 210))]),
          P.C_BLACK, "Output", stage=3, direction=(0, -1, 0.35), distance=460,
          note="Measuring CT. The DDA-1 digitally samples output current from here. [DOC]",
          metal=0.3, rough=0.6)

    guard = box(P.OUTPUT_BAY_X1 - P.OUTPUT_BAY_X0 - 16, 6,
                P.OUTPUT_BAY_Z1 - P.OUTPUT_BAY_Z0 - 16,
                center=(bay_cx, -4, (P.OUTPUT_BAY_Z0 + P.OUTPUT_BAY_Z1) / 2), r=10, r_axis="y")
    A.add("terminal_guard", "Output terminal guard", guard, (190, 200, 210, 150), "Output",
          stage=1, direction=(0, -1, 0), distance=520,
          note="Hinged insulating guard over the live output pads. [INF]", metal=0.0, rough=0.15)

    # ── 6. SCR phase-control stack ───────────────────────────────────────────
    sx0 = 1120.0
    sy0 = 420.0
    sz0 = z0 + P.PLINTH_H + 230
    hs = []
    for s in (-1, 1):
        base = box(14, P.HS_D, P.HS_H, center=(sx0 + s * (P.HS_W / 2 - 7), sy0, sz0))
        hs.append(base)
        for i in range(P.HS_FINS):
            fy = sy0 - P.HS_D / 2 + 10 + i * (P.HS_D - 20) / (P.HS_FINS - 1)
            hs.append(box(52, P.HS_FIN_T, P.HS_H - 20,
                          center=(sx0 + s * (P.HS_W / 2 - 7 - 33), fy, sz0)))
    A.add("scr_heatsinks", "SCR heatsinks", union(hs), P.C_ALU, "Power train", stage=3,
          direction=(1, 0, 0), distance=520,
          note="Extruded aluminium heatsinks clamping the thyristor stack. [INF]",
          metal=0.85, rough=0.4)

    pucks = []
    for i, dz in enumerate((-80, 0, 80)):
        pucks.append(cyl(P.SCR_PUCK_DIA / 2, P.SCR_PUCK_H, "x", (sx0, sy0, sz0 + dz), sections=36))
        pucks.append(cyl(P.SCR_PUCK_DIA / 2 - 14, P.SCR_PUCK_H + 10, "x", (sx0, sy0, sz0 + dz), sections=36))
    A.add("scr_pucks", "Thyristors (press-pack)", union(pucks), P.C_BRASS, "Power train",
          stage=3, direction=(1, 0, 0), distance=640,
          note="Press-pack SCRs. The DDA-1 fires these digitally — variable pulse time and "
               "firing angle set the output. [DOC]", metal=0.9, rough=0.3)

    clamp = union([
        box(P.HS_W + 60, 30, 30, center=(sx0, sy0, sz0 + P.HS_H / 2 + 20)),
        box(P.HS_W + 60, 30, 30, center=(sx0, sy0, sz0 - P.HS_H / 2 - 20)),
        rod((sx0 - P.HS_W / 2 - 22, sy0, sz0 - P.HS_H / 2 - 20), (sx0 - P.HS_W / 2 - 22, sy0, sz0 + P.HS_H / 2 + 20), 9),
        rod((sx0 + P.HS_W / 2 + 22, sy0, sz0 - P.HS_H / 2 - 20), (sx0 + P.HS_W / 2 + 22, sy0, sz0 + P.HS_H / 2 + 20), 9),
    ])
    A.add("scr_clamp", "Stack clamp", clamp, P.C_CABINET_DK, "Power train", stage=3,
          direction=(1, 0, 0), distance=420, note="Maintains press-pack clamping force. [INF]")

    A.add("snubber_pcb", "Gate / snubber board",
          union([box(240, 8, 150, center=(sx0, sy0 - P.HS_D / 2 - 40, sz0 + 30)),
                 box(40, 24, 24, center=(sx0 - 70, sy0 - P.HS_D / 2 - 52, sz0 + 30)),
                 box(40, 24, 24, center=(sx0 + 10, sy0 - P.HS_D / 2 - 52, sz0 + 30))]),
          P.C_PCB, "Power train", stage=3, direction=(0, -1, 0), distance=420,
          note="Gate drive and snubber network. [INF]", metal=0.1, rough=0.7)

    # ── 7. input side ────────────────────────────────────────────────────────
    A.add("input_breaker", "Input circuit breaker",
          union([box(P.MCB_W, P.MCB_D, P.MCB_H, center=(1180, 560, z0 + P.PLINTH_H + 420), r=8, r_axis="y"),
                 box(44, 30, 90, center=(1180, 560 - P.MCB_D / 2 - 15, z0 + P.PLINTH_H + 420))]),
          P.C_BLACK, "Power train", stage=3, direction=(0, 1, 0), distance=420,
          note="Main input breaker, operated by the panel CIRCUIT BREAKER switch. [DOC]",
          metal=0.2, rough=0.6)

    A.add("input_terminals", "Input terminal block",
          union([box(200, 90, 110, center=(1180, D - 120, z0 + P.PLINTH_H + 120), r=6, r_axis="z"),
                 cyl(34, 60, "y", (1180, D - 40, z0 + P.PLINTH_H + 120), sections=28)]),
          (46, 48, 54, 255), "Power train", stage=3, direction=(0, 1, 0), distance=460,
          note="460 V single-phase input, 15 ft 4/0 leads (p/n 17163). [DOC]", metal=0.2, rough=0.6)

    # ── 8. cooling ───────────────────────────────────────────────────────────
    for i, fx in enumerate((420.0, 760.0)):
        fz = zt - 230.0
        fan = [tube(P.FAN_DIA / 2, P.FAN_DIA / 2 - 18, P.FAN_DEPTH, "y", (fx, D - 90, fz), sections=44),
               cyl(44, P.FAN_DEPTH - 20, "y", (fx, D - 90, fz), sections=28)]
        for b in range(7):
            a = 2 * math.pi * b / 7
            blade = box(96, 16, 34, center=(0, 0, 0))
            blade.apply_transform(trimesh.transformations.rotation_matrix(math.radians(28), (1, 0, 0)))
            blade.apply_transform(trimesh.transformations.rotation_matrix(a, (0, 1, 0)))
            blade.apply_translation((fx + 68 * math.cos(a), D - 90, fz + 68 * math.sin(a)))
            fan.append(blade)
        A.add(f"fan_{i}", f"Cooling fan {i + 1}", union(fan), P.C_BLACK, "Cooling", stage=3,
              direction=(0, 1, 0), distance=520,
              note="Forced-air cooling. Duty is 30 min on / 30 min off. [DOC]",
              metal=0.2, rough=0.7)

    # ── 9. control electronics ───────────────────────────────────────────────
    # Sits clear behind the tilted panel's sub-chassis and clear of the fans;
    # check_clearance() in build.py enforces that.
    ECX, ECY, ECZ = 330.0, 440.0, zt - 168.0
    A.add("control_chassis", "Control electronics chassis",
          union([shell(P.ELEC_W, 240, P.ELEC_H, 1.6, (ECX, ECY, ECZ), faces="newtb"),
                 box(P.ELEC_W - 60, 1.6, P.ELEC_H - 40, center=(ECX, ECY + 124, ECZ))]),
          P.C_CABINET_DK, "Control", stage=3, direction=(-0.35, 0, 1), distance=560,
          note="Houses the DDA-1 DSP control and instrumentation boards. [DOC]")

    A.add("dda1_board", "DDA-1 processor board",
          union([box(P.ELEC_W - 80, 150, 6, center=(ECX, ECY, ECZ)),
                 box(52, 52, 12, center=(ECX - 30, ECY - 10, ECZ + 9)),
                 box(34, 34, 10, center=(ECX + 50, ECY + 18, ECZ + 8)),
                 box(120, 20, 14, center=(ECX, ECY - 58, ECZ + 10))]),
          P.C_PCB, "Control", stage=4, direction=(0, 0, 1), distance=620,
          note="Digital signal processing: full digital SCR control and digital sampling of "
               "the output current. [DOC]", metal=0.1, rough=0.7)

    A.add("psu", "Control power supply",
          shell(190, 160, 90, 1.4, (640, 450, zt - 300), faces="newtb"),
          (58, 62, 70, 255), "Control", stage=3, direction=(0.3, 0, 1), distance=380,
          note="Low-voltage supply for the control system. [INF]")

    # cable runs
    looms = []
    looms.append(rod((ECX, ECY - 125, ECZ - 40), (PANEL_CX - 120, 240, PANEL_CZ + 90), 18, 14))
    looms.append(rod((sx0, sy0 - P.HS_D / 2 - 56, sz0 + 30), (640, 450, zt - 340), 15, 14))
    looms.append(rod((1180, 560, z0 + P.PLINTH_H + 290), (cx + sw_o / 2, cy, cz - 60), 22, 14))
    looms.append(rod((cx - sw_o / 2, cy, cz - 60), (480, 470, z0 + P.PLINTH_H + 40), 22, 14))
    A.add("wiring", "Control and power wiring", union(looms), (38, 40, 46, 255), "Control",
          stage=4, direction=(0, 0, 1), distance=300, note="Representative cable runs. [INF]",
          metal=0.0, rough=0.85)

    # ── 10. documented accessory ─────────────────────────────────────────────
    stabs = [box(360, 18, 280, center=(bay_cx, -120, P.BUS_Z + 20), r=10, r_axis="y")]
    for dx in (-110, 110):
        stabs.append(box(46, 150, 24, center=(bay_cx + dx, -195, P.BUS_Z + 70)))
        stabs.append(box(46, 150, 24, center=(bay_cx + dx, -195, P.BUS_Z - 40)))
    A.add("stab_board", "Stab adapter board", union(stabs), (58, 46, 40, 255), "Accessories",
          stage=1, direction=(0, -1, 0), distance=760,
          note="Stab adapter board for drawout metal-clad breakers; used with the CBS-1 and "
               "CBS-2 stab sets. Lower loss than bolted leads. [DOC]", metal=0.1, rough=0.7)

    # Surface finish. Painted steel is a dielectric (metalness 0); only bare metal
    # gets a metallic response, which the viewer lights with an environment map.
    FINISH = {
        "core": (0.72, 0.52), "core_clamps": (0.55, 0.52), "scr_clamp": (0.55, 0.5),
        "coil_primary": (0.55, 0.52), "coil_secondary": (0.88, 0.36),
        "scr_heatsinks": (0.80, 0.42), "scr_pucks": (0.88, 0.30),
        "tow_ring": (0.72, 0.44), "lift_eyes": (0.72, 0.44),
        "rear_grille": (0.35, 0.55), "ct_output": (0.25, 0.6),
        "panel_plate": (0.10, 0.58),
    }
    PREFIX_FINISH = (
        ("caster_", (0.70, 0.46)), ("bus_", (0.90, 0.34)), ("pad_", (0.90, 0.38)),
        ("sw_", (0.72, 0.34)), ("btn_", (0.0, 0.42)), ("lamp_", (0.0, 0.28)),
        ("conn_", (0.72, 0.34)), ("sel_", (0.06, 0.48)), ("knob_", (0.06, 0.48)),
        ("meter_", (0.0, 0.46)), ("tyre_", (0.0, 0.92)),
    )
    for part in A.parts:
        fin = FINISH.get(part.name)
        if fin is None:
            for pre, f in PREFIX_FINISH:
                if part.name.startswith(pre):
                    fin = f
                    break
        if fin is None and part.name.endswith("_bezel"):
            fin = (0.72, 0.34)
        if fin:
            part.metal, part.rough = fin
    return A
