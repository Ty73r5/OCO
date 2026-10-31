#!/usr/bin/env python3
"""Build the DDA-6000 model and export it.

    python build.py                 # GLB + parts.json + STL + OBJ into ./out
    python build.py --no-stl        # skip the heavy single-body exports
"""
import argparse
import json
import os
import sys

import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dda6000 import massref, panel, params as P
from dda6000.model import DENSITY, build

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def scene(parts, unit_scale=0.001):
    """Named-node trimesh Scene, converted to glTF's metres + Y-up convention."""
    sc = trimesh.Scene()
    to_gltf = trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0))
    to_gltf[:3, :3] *= unit_scale
    for p in parts:
        m = p.mesh.copy()
        if not isinstance(m.visual, trimesh.visual.TextureVisuals):
            mat = trimesh.visual.material.PBRMaterial(
                name=p.name,
                baseColorFactor=[c / 255 for c in p.color],
                metallicFactor=p.metal,
                roughnessFactor=p.rough,
                alphaMode="BLEND" if p.color[3] < 255 else "OPAQUE",
            )
            m.visual = trimesh.visual.TextureVisuals(material=mat)
        m.apply_transform(to_gltf)
        sc.add_geometry(m, node_name=p.name, geom_name=p.name)
    return sc


def metadata(parts, unit_scale=0.001):
    """Explode vectors and part facts for the viewer (metres, Y-up)."""
    out = []
    total = 0.0
    acc = 0.0
    for p in parts:
        mat = massref.material(p.name)
        vol = abs(p.mesh.volume) * massref.FILL.get(p.name, 1.0) * 1e-9  # mm^3 -> m^3
        mass = vol * DENSITY[mat]
        if p.group == "Accessories":
            acc += mass
        else:
            total += mass
        d = np.array(p.direction, float)
        n = np.linalg.norm(d)
        d = d / n if n > 1e-9 else np.array([0.0, 0.0, 1.0])
        c = p.mesh.bounds.mean(axis=0)
        out.append({
            "name": p.name, "label": p.label, "group": p.group, "stage": p.stage,
            "dir": [float(d[0]), float(d[2]), float(-d[1])],     # model Z-up -> glTF Y-up
            "dist": p.distance * unit_scale,
            "centre": [float(c[0] * unit_scale), float(c[2] * unit_scale), float(-c[1] * unit_scale)],
            "mass": round(mass, 2), "material": mat, "note": p.note,
        })
    return out, total, acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-stl", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    A = build()
    parts = A.parts
    meta, total, acc = metadata(parts)

    sc = scene(parts)
    glb = os.path.join(OUT, "dda6000.glb")
    with open(glb, "wb") as f:
        f.write(sc.export(file_type="glb"))

    json.dump({
        "model": "Megger DDA-6000 Universal Circuit Breaker Test Set",
        "units": "metres",
        "envelope_mm": {"w": P.W, "d": P.D, "h": P.H},
        "documented_mass_kg": P.MASS_KG,
        "modelled_mass_kg": round(total, 1),
        "parts": meta,
    }, open(os.path.join(OUT, "parts.json"), "w"), indent=1)

    panel.texture().save(os.path.join(OUT, "panel_artwork.png"))

    if not a.no_stl:
        merged = trimesh.util.concatenate([p.mesh for p in parts])
        merged.export(os.path.join(OUT, "dda6000.stl"))
        merged.export(os.path.join(OUT, "dda6000.obj"))

    b = A.bounds()
    print(f"parts            {len(parts)}")
    print(f"triangles        {sum(len(p.mesh.faces) for p in parts):,}")
    print(f"bounds mm        X {b[0][0]:.0f}..{b[1][0]:.0f}  "
          f"Y {b[0][1]:.0f}..{b[1][1]:.0f}  Z {b[0][2]:.0f}..{b[1][2]:.0f}")
    print(f"documented size  {P.W:.0f} x {P.D:.0f} x {P.H:.0f} mm (55 x 28 x 46 in)")
    print(f"documented mass  {P.MASS_KG:.0f} kg")
    print(f"modelled mass    {total:.0f} kg  ({100 * total / P.MASS_KG - 100:+.0f}%)")
    print(f"accessories      {acc:.0f} kg (not counted in the figure above)")
    heavy = sorted((m for m in meta if m["group"] != "Accessories"), key=lambda m: -m["mass"])[:8]
    for h in heavy:
        print(f"   {h['mass']:7.1f} kg  {h['label']}")
    print(f"wrote            {glb}  ({os.path.getsize(glb) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
