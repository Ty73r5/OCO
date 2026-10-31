# Megger DDA-6000 — parametric 3D model

A parametric, explodable 3D model of the Megger DDA-6000 Universal Circuit Breaker
Test Set: a 60 000 A primary-injection test set. 71 named parts, built from code,
exported to GLB / STL / OBJ, with an interactive exploded-view viewer.

```
python3 build.py        # -> out/dda6000.glb, .stl, .obj, parts.json, panel_artwork.png
python3 export_web.py   # -> out/model_web.json  (payload for viewer/index.html)
```

## What is accurate, and what is not

This matters more than the render, so it is stated first.

**Taken from Megger's published figures** — datasheet and instruction manual for the
DDA-3000 / DDA-6000 (Part No. 17177 Rev. 5):

| | |
|---|---|
| Overall size | 46 × 55 × 28 in → 1168 × 1397 × 711 mm (H × W × D) |
| Mass | 1200 lb (545 kg) |
| Enclosure | sheet metal, low centre of gravity, tow ring, lifting eyes, large locking swivel casters (all four swivel, all four lock) |
| Output | 60 000 A instantaneous maximum |
| Input | 460 V single phase |
| Duty | rated continuous current, 30 min on / 30 min off |
| Control system | DDA-1, DSP-based: full digital SCR control, digital sampling of output current |
| Metering | 5-digit displays, 0.281 in (7 mm) numerals; memory ammeter, timer, voltmeter |
| Ammeter ranges | 200 / 2 000 / 20 000 / 200 000 A, 200 kA default |
| Ammeter modes | MEM / CONT |
| Output control | multi-position OUTPUT SELECTOR (coarse) + VERNIER CONTROL (fine); variable pulse time and firing angle |
| Buttons | START (energises output), STOP (de-energises) |
| Lamps | OUTPUT ENERGIZED, THERMAL WARNING, THERMAL SHUTDOWN, GROUND INTERLOCK, OVER RANGE |
| Other | input circuit breaker ON/OFF, external (remote) initiate circuit, stab adapter board with CBS-1 / CBS-2 stab sets, 15 ft 4/0 input leads (p/n 17163), 10 ft 4/0 interconnect leads (p/n 17164) |

Every one of those controls exists on the modelled panel, with its real legend.

**Inferred.** No drawing, photograph or teardown of this set was reachable from the
machine that built the model, so the following are engineering reconstructions, not
measurements:

- the layout of components inside the cabinet;
- transformer and SCR-stack geometry;
- the arrangement of the controls on the panel (the control *set* is documented, its
  positions are not);
- sheet-metal detailing, and the colour.

Parts carry their own provenance: `note` ends with `[DOC]` or `[INF]`, and the viewer
tags each part **Documented** or **Inferred**.

**The mass check.** The one hard constraint on hidden volumes is the published 545 kg.
`build.py` assigns each part a material and a fill factor (a drawn solid standing in for
channel, tube or wound section), sums the mass and prints it against the published
figure. The model currently lands at **566 kg, +4%**, with the transformer at 284 kg of
that. This is a sanity check on the reconstruction, not a claim of accuracy.

## Layout

| Path | |
|---|---|
| `dda6000/params.py` | every dimension, each tagged `[DOC]` or `[INF]` |
| `dda6000/prims.py` | geometry primitives, `Part` / `Assembly` |
| `dda6000/panel.py` | control-panel layout table + silkscreen artwork (drives both the texture and the 3-D hardware) |
| `dda6000/model.py` | the 71-part assembly |
| `dda6000/massref.py` | material and fill factor per part |
| `build.py` | GLB / STL / OBJ export + mass report |
| `export_web.py` | compact payload for the viewer |
| `viewer/index.html` | interactive exploded-view viewer |

## Exploded view

Each part carries an explosion direction, distance and stage. The viewer's single
slider runs the four stages in sequence:

1. **Skins off** — covers, louvers, grille, lifting eyes, terminal guard
2. **Panel apart** — faceplate, then every knob, lamp, meter and button off it
3. **Subassemblies out** — SCR stack, output bus and pads, CT, fans, input breaker, electronics
4. **Core stripped** — windings lifted off the core, frame and skid away, casters down

The transformer core sits at distance 0: it is the datum everything else moves away from.

## Viewer

`viewer/index.html` loads `model.json` (rename `out/model_web.json`) and needs one
external script, three.js. Orbit controls and the explode logic are hand-written, so
there are no loader or control add-ons to fetch. Click any part for its mass, material
and provenance; toggle assemblies; X-ray the skins; overlay the published dimensions.

## Using the model elsewhere

`out/dda6000.glb` keeps all 71 parts as separately named nodes, so Blender, Houdini,
three.js or any glTF viewer can explode it using the vectors in `out/parts.json`.
`dda6000.stl` and `dda6000.obj` are single merged bodies for printing or import into CAD.
Units: millimetres in the source model and the STL/OBJ; metres in the GLB and the web
payload, Y-up, as glTF requires.
