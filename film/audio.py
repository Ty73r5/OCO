"""Procedural ambient score + narration mix.

Score: slow additive-synthesis pads (per-chapter chord progressions), sub drone, sparse bells,
convolution reverb. Mix: narration placed per the timeline, music ducked under the voice.
"""
import json
import os

import numpy as np
import soundfile as sf
from scipy.signal import oaconvolve, resample_poly

from common_paths import MEDIA
import plan as P

SR = 48000
OUT = os.path.join(MEDIA, "audio")
os.makedirs(OUT, exist_ok=True)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# chord progressions per chapter (MIDI notes); each chord ~10 s
PROG = {
    0: [[50, 57, 62, 65, 69, 76], [46, 53, 58, 62, 69, 74], [41, 48, 57, 60, 64, 72], [48, 55, 60, 64, 67, 74]],
    1: [[45, 52, 57, 60, 64, 71], [41, 48, 53, 57, 64, 69], [48, 55, 60, 64, 67, 72], [43, 50, 55, 59, 62, 69]],
    2: [[40, 47, 52, 55, 59, 66], [36, 43, 48, 52, 55, 62], [43, 50, 55, 59, 62, 69], [38, 45, 50, 54, 57, 64]],
    3: [[41, 48, 53, 57, 59, 64], [43, 50, 55, 59, 62, 67], [45, 52, 57, 60, 64, 71], [41, 48, 55, 57, 64, 67]],
    4: [[38, 45, 50, 54, 57, 64], [43, 50, 55, 59, 62, 66], [47, 54, 59, 62, 66, 69], [45, 52, 57, 61, 64, 69]],
    5: [[36, 43, 48, 51, 55, 62], [44, 51, 56, 60, 63, 70], [41, 48, 53, 56, 60, 67], [43, 50, 55, 59, 62, 67]],
    6: [[45, 52, 57, 60, 64, 67], [41, 48, 53, 57, 60, 67], [43, 50, 55, 59, 62, 69], [40, 47, 52, 55, 59, 64]],
    7: [[42, 49, 54, 57, 61, 68], [38, 45, 50, 54, 57, 64], [40, 47, 52, 56, 59, 66], [37, 44, 49, 52, 56, 61]],
    8: [[40, 47, 52, 55, 59, 66], [43, 50, 55, 59, 62, 67], [36, 43, 48, 52, 55, 62], [38, 45, 50, 54, 57, 66]],
    9: [[43, 50, 55, 59, 62, 69], [40, 47, 52, 55, 59, 64], [36, 43, 48, 52, 55, 64], [38, 45, 50, 54, 57, 62]],
    10: [[36, 43, 48, 51, 55, 60], [44, 51, 56, 60, 63, 68], [39, 46, 51, 55, 58, 65], [43, 50, 55, 59, 62, 65]],
    11: [[38, 45, 50, 54, 57, 64, 69], [43, 50, 55, 59, 62, 69, 74], [47, 54, 59, 62, 66, 71], [45, 52, 57, 61, 64, 69, 76]],
    12: [[38, 45, 50, 54, 57, 64], [46, 53, 58, 62, 65, 72], [43, 50, 55, 59, 62, 69], [45, 52, 57, 61, 64, 71]],
}
BELLS = {k: sorted(set(n % 12 for c in v for n in c)) for k, v in PROG.items()}


def pad_note(f, n, rng, bright=1.0):
    t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    for k in range(1, 7):
        amp = (1.0 / k ** 1.6) * (bright if k > 2 else 1.0)
        if f * k > 9000:
            break
        for ch, det in ((0, -0.0012), (1, 0.0012)):
            ph = rng.random() * 2 * np.pi
            lfo = 1 + 0.0007 * np.sin(2 * np.pi * (0.11 + 0.05 * rng.random()) * t + rng.random() * 6)
            out[:, ch] += amp * np.sin(2 * np.pi * f * k * (1 + det) * t * lfo + ph).astype(np.float32)
    trem = 0.8 + 0.2 * np.sin(2 * np.pi * (0.05 + 0.04 * rng.random()) * t + rng.random() * 6)
    return out * trem[:, None].astype(np.float32)


def envelope(n, att, rel):
    e = np.ones(n, np.float32)
    a, r = int(att * SR), int(rel * SR)
    e[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    e[-r:] = np.cos(np.linspace(0, np.pi / 2, r)) ** 2
    return e


def bell(f, n, rng):
    t = np.arange(n) / SR
    s = np.zeros(n, np.float32)
    for ratio, amp, dec in ((1.0, 1.0, 2.8), (2.76, 0.35, 1.4), (5.4, 0.12, 0.7), (2.0, 0.25, 2.0)):
        s += (amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / dec)).astype(np.float32)
    s *= (1 - np.exp(-t / 0.004)).astype(np.float32)
    pan = rng.uniform(0.25, 0.75)
    return np.stack([s * (1 - pan), s * pan], -1)


def reverb_ir(seconds=4.5, seed=0):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)).astype(np.float32) * np.exp(-t / 1.1)[:, None].astype(np.float32)
    # darken the tail
    from scipy.signal import butter, lfilter
    b, a = butter(2, 3500 / (SR / 2))
    ir = lfilter(b, a, ir, axis=0).astype(np.float32)
    ir[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]
    return ir / np.sqrt((ir ** 2).sum(0, keepdims=True))


def chapter_music(ch, dur, seed):
    rng = np.random.default_rng(seed)
    n = int(dur * SR) + SR * 6
    buf = np.zeros((n, 2), np.float32)
    prog = PROG[ch]
    cl = 11.0 if ch != 11 else 8.0
    t0, i = 0.0, 0
    while t0 < dur + 2:
        chord = prog[i % len(prog)]
        ln = cl + 5.0
        m = int(ln * SR)
        s0 = int(t0 * SR)
        e = envelope(m, 3.5, 5.0)
        seg = np.zeros((m, 2), np.float32)
        for j, note in enumerate(chord):
            v = 0.55 if j == 0 else (0.38 if note < 60 else 0.24)
            seg += pad_note(mtof(note), m, rng, bright=0.8 if ch != 11 else 1.1) * v
        # sub drone on the root
        tt = np.arange(m) / SR
        sub = 0.35 * np.sin(2 * np.pi * mtof(chord[0] - 12) * tt).astype(np.float32)
        seg += np.stack([sub, sub], -1)
        end = min(s0 + m, n)
        buf[s0:end] += (seg * e[:, None])[: end - s0]
        t0 += cl
        i += 1
    # sparse bells
    pcs = BELLS[ch]
    t = rng.uniform(2, 6)
    while t < dur:
        pc = pcs[rng.integers(len(pcs))]
        note = 72 + pc + (12 if rng.random() < 0.3 else 0)
        m = int(6 * SR)
        s0 = int(t * SR)
        end = min(s0 + m, n)
        buf[s0:end] += (bell(mtof(note), m, rng) * (0.10 if ch != 11 else 0.16))[: end - s0]
        t += rng.uniform(3.5, 9.0) if ch != 11 else rng.uniform(1.8, 4.0)
    return buf


def build():
    pl, T = P.plan()
    chapters = []
    for x in pl:
        ch = x["sc"]["chapter"]
        if not chapters or chapters[-1][0] != ch:
            chapters.append([ch, x["start"], x["start"] + x["dur"]])
        else:
            chapters[-1][2] = x["start"] + x["dur"]
    N = int(T * SR) + SR * 2
    music = np.zeros((N, 2), np.float32)
    ir = reverb_ir()
    xf = 3.0
    for k, (ch, a, b) in enumerate(chapters):
        a0 = max(a - xf / 2, 0)
        dur = b - a0 + xf
        m = chapter_music(ch, dur, seed=ch * 7 + 1)
        wet = oaconvolve(m, ir, axes=0)[: len(m)].astype(np.float32)
        m = 0.55 * m + 0.9 * wet
        e = envelope(len(m), xf, xf)
        s0 = int(a0 * SR)
        end = min(s0 + len(m), N)
        music[s0:end] += (m * e[:, None])[: end - s0]
        print("chapter", ch, round(dur, 1), flush=True)
    music /= np.percentile(np.abs(music), 99.9) + 1e-6

    # narration track
    voice = np.zeros(N, np.float32)
    for x in pl:
        if not x["meta"]:
            continue
        v, sr = sf.read(os.path.join(MEDIA, "voice", x["sc"]["id"] + ".wav"), dtype="float32")
        v = resample_poly(v, SR, sr).astype(np.float32)
        s0 = int(x["voice_at"] * SR)
        voice[s0:s0 + len(v)] += v[: N - s0]
    voice /= np.percentile(np.abs(voice), 99.95) + 1e-6
    voice *= 0.89

    # ducking envelope from narration
    hop = 480
    env = np.sqrt(np.convolve(voice ** 2, np.ones(hop) / hop, mode="same")[::hop])
    act = (env > 0.02).astype(np.float32)
    # smooth: fast attack, slow release
    g = np.zeros_like(act)
    cur = 0.0
    for i, a in enumerate(act):
        cur = cur + (a - cur) * (0.25 if a > cur else 0.012)
        g[i] = cur
    level = np.ones_like(g) * 0.30  # music bed under the voice
    # louder where no narration for a while (title, chapter cards, interlude, credits)
    level = 0.30 * g + 0.62 * (1 - g)
    gain = np.repeat(level, hop)[:N]
    gain = np.pad(gain, (0, max(0, N - len(gain))), constant_values=level[-1])[:N]
    mix = music * gain[:, None] * 0.55 + voice[:, None]
    # fade in/out
    fi, fo = int(3 * SR), int(6 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    end = int(T * SR)
    mix[end - fo:end] *= np.linspace(1, 0, fo)[:, None]
    mix[end:] = 0
    mix = mix[:end]
    peak = np.abs(mix).max()
    mix *= 0.95 / peak
    out = os.path.join(OUT, "mix.wav")
    sf.write(out, mix, SR, subtype="PCM_16")
    sf.write(os.path.join(OUT, "music.wav"), (music[:end] * 0.5).astype(np.float32), SR, subtype="PCM_16")
    print("wrote", out, T)


if __name__ == "__main__":
    build()
