"""Render single frames of a scene for inspection: python preview.py SCENE_ID t [t ...] [--dur D]"""
import os
import sys

from PIL import Image

from common_paths import WORK
from render.registry import make
import script

OUT = os.path.join(WORK, "preview")
os.makedirs(OUT, exist_ok=True)

if __name__ == "__main__":
    args = sys.argv[1:]
    dur = 20.0
    if "--dur" in args:
        i = args.index("--dur")
        dur = float(args[i + 1])
        del args[i:i + 2]
    sid, ts = args[0], [float(x) for x in args[1:]] or [dur / 2]
    sc = next(s for s in script.S if s["id"] == sid)
    scene = make(sc, dur)
    for t in ts:
        a = scene.frame(t)
        p = os.path.join(OUT, f"{sid}_{t:05.1f}.jpg")
        Image.fromarray(a).save(p, quality=88)
        print(p)
