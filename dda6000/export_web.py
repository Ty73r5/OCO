#!/usr/bin/env python3
"""Pack the model into a single compact JSON payload for the web viewer.

Geometry ships as base64 typed arrays (positions + 16-bit indices, flat-shaded in
the viewer so no normals are needed), which keeps the page to one external
script — three.js itself — with no loader or control add-ons.
"""
import base64
import io
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dda6000 import massref, panel, params as P
from dda6000.model import DENSITY, build

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
SCALE = 0.001                      # mm -> metres
TEX_W = 1856                       # panel texture width in the web build


def b64(arr):
    return base64.b64encode(arr.tobytes()).decode("ascii")


def main():
    os.makedirs(OUT, exist_ok=True)
    A = build()
    parts, total, acc = [], 0.0, 0.0

    for p in A.parts:
        m = p.mesh
        v = np.asarray(m.vertices, np.float64)
        f = np.asarray(m.faces, np.int64)
        # model is Z-up, millimetres; the viewer is Y-up, metres
        pos = np.stack([v[:, 0], v[:, 2], -v[:, 1]], axis=1) * SCALE
        if len(v) > 65535:
            # split is never needed at this size, but fail loudly rather than silently wrap
            raise ValueError(f"{p.name}: {len(v)} vertices exceeds uint16 indices")

        mat = massref.material(p.name)
        mass = abs(m.volume) * massref.FILL.get(p.name, 1.0) * 1e-9 * DENSITY[mat]
        if p.group == "Accessories":
            acc += mass
        else:
            total += mass

        d = np.array(p.direction, float)
        n = np.linalg.norm(d)
        d = d / n if n > 1e-9 else np.array([0.0, 0.0, 1.0])

        rec = {
            "name": p.name, "label": p.label, "group": p.group, "stage": p.stage,
            "dir": [round(float(d[0]), 4), round(float(d[2]), 4), round(float(-d[1]), 4)],
            "dist": round(p.distance * SCALE, 4),
            "color": [round(c / 255, 4) for c in p.color[:3]],
            "opacity": round(p.color[3] / 255, 3),
            "metal": p.metal, "rough": p.rough,
            "mass": round(mass, 2), "material": mat, "note": p.note,
            "tris": int(len(f)),
            "pos": b64(pos.astype(np.float32)),
            "idx": b64(f.astype(np.uint16)),
        }
        if hasattr(m.visual, "uv") and m.visual.uv is not None and len(m.visual.uv) == len(v):
            rec["uv"] = b64(np.asarray(m.visual.uv, np.float32))
            rec["tex"] = True
        parts.append(rec)

    tex = panel.texture()
    tex = tex.resize((TEX_W, int(TEX_W * tex.size[1] / tex.size[0])))
    buf = io.BytesIO()
    tex.save(buf, format="PNG", optimize=True)
    tex_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    payload = {
        "model": "Megger DDA-6000",
        "subtitle": "Universal Circuit Breaker Test Set",
        "envelope_mm": [P.W, P.D, P.H],
        "envelope_in": [55, 28, 46],
        "documented_mass_kg": P.MASS_KG,
        "modelled_mass_kg": round(total, 1),
        "accessory_mass_kg": round(acc, 1),
        "maxStage": max(p["stage"] for p in parts),
        "texture": "data:image/png;base64," + tex_b64,
        "parts": parts,
    }
    path = os.path.join(OUT, "model_web.json")
    json.dump(payload, open(path, "w"), separators=(",", ":"))
    print(f"parts     {len(parts)}")
    print(f"triangles {sum(p['tris'] for p in parts):,}")
    print(f"texture   {len(tex_b64) / 1e3:.0f} kB (base64)")
    print(f"payload   {os.path.getsize(path) / 1e6:.2f} MB  -> {path}")


if __name__ == "__main__":
    main()
