"""Film timeline: scene durations from narration length plus padding."""
import json
import os

from common_paths import MEDIA
import script

PAD_IN, PAD_OUT = 0.9, 1.5
XFADE = 0.5


def voice_meta(sid):
    p = os.path.join(MEDIA, "voice", sid + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def plan():
    out, T = [], 0.0
    for sc in script.S:
        m = voice_meta(sc["id"]) if sc["text"] else None
        vd = m["dur"] if m else 0.0
        dur = (PAD_IN + vd + PAD_OUT if sc["text"] else 0.0) + sc["hold"]
        out.append(dict(sc=sc, start=T, dur=round(dur * 24) / 24, voice_at=T + PAD_IN, voice_dur=vd, meta=m))
        T += out[-1]["dur"]
    return out, T


if __name__ == "__main__":
    p, T = plan()
    for x in p:
        print(f"{x['start']/60:6.2f}  {x['dur']:6.1f}  {x['sc']['id']}")
    print("TOTAL", T / 60, "min")
