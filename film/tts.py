"""Narration: Kokoro (open-weight TTS) per sentence, with timings for subtitles."""
import json
import os
import re
import sys

import numpy as np
import soundfile as sf

from common_paths import MEDIA, MODELS
import script

VOICE = os.environ.get("OCO_VOICE", "af_heart")
SPEED = float(os.environ.get("OCO_SPEED", "0.93"))
SR = 24000
OUT = os.path.join(MEDIA, "voice")
os.makedirs(OUT, exist_ok=True)

SAY = {  # spoken forms
    "NOAA": "Noah", "TROPOMI": "Tropomi", "GOSAT": "Go-sat", "Indo Gangetic": "Indo-Gangetic",
    "re emits": "re-emits", "X C O two": "X, C, O two",
}
SHOW = {  # subtitle forms
    "O C O two": "OCO-2", "O C O three": "OCO-3", "O C O": "OCO", "X C O two": "XCO2", "C O two M": "CO2M",
    "GOSAT G W": "GOSAT-GW", "GOSAT two": "GOSAT-2", "GOES nineteen": "GOES-19", "Sentinel five P": "Sentinel-5P",
    "Delta Two": "Delta II", "re emits": "re-emits", "Indo Gangetic": "Indo-Gangetic", "super emitters": "super-emitters",
}


def sentences(text):
    parts = re.split(r"(?<=[.?!])\s+", text.strip())
    return [p for p in parts if p]


def apply(m, s):
    for a, b in sorted(m.items(), key=lambda kv: -len(kv[0])):
        s = s.replace(a, b)
    return s


def main(only=None):
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    for sc in script.S:
        if not sc["text"] or (only and sc["id"] not in only):
            continue
        wav = os.path.join(OUT, sc["id"] + ".wav")
        meta = os.path.join(OUT, sc["id"] + ".json")
        if os.path.exists(meta) and json.load(open(meta)).get("text") == sc["text"] and not only:
            continue
        chunks, cues, t = [], [], 0.0
        for i, sent in enumerate(sentences(sc["text"])):
            audio, sr = k.create(apply(SAY, sent), voice=VOICE, speed=SPEED, lang="en-us")
            assert sr == SR
            audio = np.asarray(audio, np.float32)
            # trim leading/trailing near-silence so pauses are controlled here
            nz = np.nonzero(np.abs(audio) > 0.004)[0]
            if len(nz):
                audio = audio[max(nz[0] - 240, 0): nz[-1] + 1200]
            gap = 0.42 if not sent.endswith("?") else 0.5
            cues.append(dict(start=t, end=t + len(audio) / SR, text=apply(SHOW, sent)))
            chunks += [audio, np.zeros(int(gap * SR), np.float32)]
            t += len(audio) / SR + gap
        a = np.concatenate(chunks[:-1])
        sf.write(wav, a, SR)
        json.dump(dict(text=sc["text"], dur=len(a) / SR, cues=cues), open(meta, "w"), indent=1)
        print(sc["id"], round(len(a) / SR, 1), flush=True)


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
