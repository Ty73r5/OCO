"""Geometry primitives.

Model coordinate system (millimetres, Z up, right-handed):
    +X  cabinet left  -> right   (0 .. W)
    +Y  cabinet front -> back    (0 .. D, Y=0 is the operator's side)
    +Z  floor         -> up      (0 .. H)
Converted to glTF's Y-up convention only at export time.
"""
from dataclasses import dataclass, field

import numpy as np
import shapely.affinity as sa
import shapely.geometry as sg
import trimesh

AXES = {"x": (0, 1, 2), "y": (1, 0, 2), "z": (2, 0, 1)}


def rrect(w, h, r=0.0, cx=0.0, cy=0.0):
    """Rounded rectangle polygon centred on (cx, cy)."""
    r = min(r, w / 2 - 1e-6, h / 2 - 1e-6) if r > 0 else 0.0
    p = sg.box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    if r > 0:
        p = p.buffer(-r, join_style=2).buffer(r, join_style=1, resolution=6)
    return p


def _orient(mesh, t, axis, center):
    """Extrusion comes out along +Z spanning 0..t; move to `axis` and `center`."""
    mesh.apply_translation((0, 0, -t / 2.0))
    if axis == "x":
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    elif axis == "y":
        mesh.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))
    mesh.apply_translation(center)
    return mesh


def prism(poly, t, axis="z", center=(0, 0, 0)):
    """Extrude a shapely polygon by `t` along `axis`, centred at `center`.

    The polygon's (u, v) always land on the two world axes that are not `axis`,
    in ascending order and without mirroring:
        axis "z" -> (u, v) = (x, y)
        axis "y" -> (u, v) = (x, z)
        axis "x" -> (u, v) = (y, z)
    """
    if axis == "y":
        poly = sa.affine_transform(poly, [1, 0, 0, -1, 0, 0])   # (u, v) -> (u, -v)
    elif axis == "x":
        poly = sa.affine_transform(poly, [0, -1, 1, 0, 0, 0])   # (u, v) -> (-v, u)
    m = trimesh.creation.extrude_polygon(poly, float(t))
    return _orient(m, t, axis, center)


def box(w, d, h, center=(0, 0, 0), r=0.0, r_axis="z"):
    """Axis-aligned box of size (w, d, h). `r` rounds the corners in the plane
    normal to `r_axis`."""
    if r <= 0:
        m = trimesh.creation.box((w, d, h))
        m.apply_translation(center)
        return m
    if r_axis == "z":
        return prism(rrect(w, d, r), h, "z", center)
    if r_axis == "y":
        return prism(rrect(w, h, r), d, "y", center)
    return prism(rrect(d, h, r), w, "x", center)


def cyl(radius, length, axis="z", center=(0, 0, 0), sections=48):
    m = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    return _orient(m, length, axis, center)


def tube(r_out, r_in, length, axis="z", center=(0, 0, 0), sections=48):
    poly = sg.Point(0, 0).buffer(r_out, resolution=sections // 4)
    poly = poly.difference(sg.Point(0, 0).buffer(r_in, resolution=sections // 4))
    return prism(poly, length, axis, center)


def rod(p0, p1, radius, sections=20):
    """Cylinder between two points."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    v = p1 - p0
    L = float(np.linalg.norm(v))
    m = trimesh.creation.cylinder(radius=radius, height=L, sections=sections)
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / L))
    m.apply_translation((p0 + p1) / 2.0)
    return m


def union(meshes):
    ms = [m for m in meshes if m is not None and len(m.faces)]
    if not ms:
        return None
    return trimesh.util.concatenate(ms)


def stud(center, axis="y", dia=16.0, length=46.0, head=False):
    parts = [cyl(dia / 2, length, axis, center, sections=16)]
    if head:
        n = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
        c = np.asarray(center, float) + np.asarray(n) * (length / 2 - 6)
        parts.append(cyl(dia * 0.82, 11.0, axis, c, sections=6))
    return union(parts)


def louvers(x0, x1, z0, z1, y, depth, slot_h, pitch, thickness=2.6):
    """Bank of stamped louvers as a set of thin angled blades."""
    out = []
    z = z0
    while z + slot_h <= z1:
        blade = box(x1 - x0, depth, thickness, center=(0, 0, 0))
        blade.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(32), (1, 0, 0)))
        blade.apply_translation(((x0 + x1) / 2, y + depth * 0.25, z + slot_h / 2))
        out.append(blade)
        z += pitch
    return union(out)


@dataclass
class Part:
    """One exploded-view component."""
    name: str                       # unique node name
    label: str                      # human-readable
    mesh: object
    color: tuple
    group: str                      # assembly group for the viewer tree
    stage: int = 1                  # explosion stage, 0 = never moves
    direction: tuple = (0, 0, 1)    # unit vector it flies along
    distance: float = 400.0         # mm at full explode
    note: str = ""                  # provenance / description
    source: str = "INF"             # DOC or INF
    metal: float = 0.0      # painted / dielectric by default
    rough: float = 0.52


class Assembly:
    def __init__(self):
        self.parts = []
        self._names = set()

    def add(self, name, label, mesh, color, group, **kw):
        if mesh is None or not len(mesh.faces):
            raise ValueError(f"empty mesh for {name}")
        if name in self._names:
            raise ValueError(f"duplicate part name {name}")
        self._names.add(name)
        mesh.update_faces(mesh.nondegenerate_faces())
        mesh.remove_unreferenced_vertices()
        self.parts.append(Part(name, label, mesh, color, group, **kw))
        return self.parts[-1]

    def bounds(self):
        b = np.array([p.mesh.bounds for p in self.parts])
        return np.array([b[:, 0].min(axis=0), b[:, 1].max(axis=0)])


def textured_plate(w, h, t, image, uv_face="-y"):
    """Flat plate of size (w, h) and thickness `t`, built in the XZ plane with
    its front face at -Y carrying `image` stretched across it. Other faces take
    a corner pixel so they read as panel colour."""
    hw, hh, ht = w / 2.0, h / 2.0, t / 2.0
    v, f, uv = [], [], []

    def quad(p0, p1, p2, p3, uvs):
        i = len(v)
        v.extend([p0, p1, p2, p3])
        uv.extend(uvs)
        f.extend([[i, i + 1, i + 2], [i, i + 2, i + 3]])

    e = (0.003, 0.003)
    # front (-Y) carries the artwork; v flipped because image rows run downward
    quad((-hw, -ht, -hh), (hw, -ht, -hh), (hw, -ht, hh), (-hw, -ht, hh),
         [(0, 1), (1, 1), (1, 0), (0, 0)])
    quad((hw, ht, -hh), (-hw, ht, -hh), (-hw, ht, hh), (hw, ht, hh), [e] * 4)
    quad((-hw, ht, -hh), (-hw, -ht, -hh), (-hw, -ht, hh), (-hw, ht, hh), [e] * 4)
    quad((hw, -ht, -hh), (hw, ht, -hh), (hw, ht, hh), (hw, -ht, hh), [e] * 4)
    quad((-hw, -ht, hh), (hw, -ht, hh), (hw, ht, hh), (-hw, ht, hh), [e] * 4)
    quad((-hw, ht, -hh), (hw, ht, -hh), (hw, -ht, -hh), (-hw, -ht, -hh), [e] * 4)

    mesh = trimesh.Trimesh(vertices=np.array(v, float), faces=np.array(f), process=False)
    mat = trimesh.visual.material.PBRMaterial(
        baseColorTexture=image, metallicFactor=0.15, roughnessFactor=0.55, name="panel")
    mesh.visual = trimesh.visual.TextureVisuals(uv=np.array(uv, float), material=mat)
    return mesh


def shell(w, d, h, t, center, faces="nsewtb", r=0.0):
    """Hollow sheet-metal box built from plates, so its volume is honest.
    `faces`: n=+Y back, s=-Y front, e=+X, w=-X, t=+Z top, b=-Z bottom."""
    cx, cy, cz = center
    out = []
    if "n" in faces:
        out.append(box(w, t, h, (cx, cy + d / 2 - t / 2, cz), r, "y"))
    if "s" in faces:
        out.append(box(w, t, h, (cx, cy - d / 2 + t / 2, cz), r, "y"))
    if "w" in faces:
        out.append(box(t, d - 2 * t, h, (cx - w / 2 + t / 2, cy, cz)))
    if "e" in faces:
        out.append(box(t, d - 2 * t, h, (cx + w / 2 - t / 2, cy, cz)))
    if "t" in faces:
        out.append(box(w - 2 * t, d - 2 * t, t, (cx, cy, cz + h / 2 - t / 2)))
    if "b" in faces:
        out.append(box(w - 2 * t, d - 2 * t, t, (cx, cy, cz - h / 2 + t / 2)))
    return union(out)
