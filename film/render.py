"""Render the film: scenes in parallel → x264 segments → concat with audio + subtitles."""
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np

from common_paths import MEDIA
import plan as P
from render.base import FPS, H, MUTED, W, blend, draw_text, font, to_np, to_pil
from render.registry import make

SEG = os.path.join(MEDIA, "segments")
os.makedirs(SEG, exist_ok=True)
XF = 12  # crossfade frames into the next scene
NO_COUNTER = {"starfield", "title", "chapter_card", "counter_intro", "counter_final", "credits"}
RATE = 43.184e9 / (365.25 * 86400)


def counter_overlay(img, tg, t_counter0, alpha=1.0):
    im = to_pil(img)
    v = RATE * (tg - t_counter0)
    draw_text(im, (W - 56, 52), "CO₂ RELEASED SINCE THIS FILM BEGAN", font(17, "Medium"), fill=MUTED, anchor="rs", alpha=0.9 * alpha, spacing=2)
    draw_text(im, (W - 56, 92), f"{int(v):,} t", font(38, "Light"), fill=(255, 196, 140), anchor="rs", alpha=alpha)
    return to_np(im)


def render_scene(args):
    i, out = args
    pl, T = P.plan()
    x = pl[i]
    sc = x["sc"]
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return i, 0.0
    t_counter0 = next(y["start"] for y in pl if y["sc"]["id"] == "open_counter")
    t_counter_end = next(y["start"] for y in pl if y["sc"]["id"] == "c12_counter")
    scene = make(sc, x["dur"])
    scene.T0, scene.COUNTER_T0 = x["start"], t_counter0
    nxt = None
    if i + 1 < len(pl):
        y = pl[i + 1]
        ns = make(y["sc"], y["dur"])
        ns.T0, ns.COUNTER_T0 = y["start"], t_counter0
        nf = ns.frame(0.0)
        if y["sc"]["visual"] not in NO_COUNTER and t_counter0 + 2 < y["start"] < t_counter_end:
            nf = counter_overlay(nf, y["start"], t_counter0)
        nxt = nf
    n = int(round(x["dur"] * FPS))
    tmp = out + ".part.mp4"
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-g", "48",
                           "-threads", "2", tmp], stdin=subprocess.PIPE)
    t0 = time.time()
    show_counter = sc["visual"] not in NO_COUNTER
    for k in range(n):
        t = k / FPS
        img = scene.frame(t)
        tg = x["start"] + t
        if show_counter and t_counter0 + 2 < tg < t_counter_end:
            a = min(1.0, (tg - t_counter0 - x["dur"] * 0 - 2) / 1.0) if x["start"] <= t_counter0 + 30 else 1.0
            img = counter_overlay(img, tg, t_counter0, alpha=max(0.0, min(a, 1.0)))
        if nxt is not None and k >= n - XF:
            img = blend(img, nxt, (k - (n - XF) + 1) / (XF + 1))
        ff.stdin.write(np.ascontiguousarray(img, dtype=np.uint8).tobytes())
    ff.stdin.close()
    ff.wait()
    os.replace(tmp, out)
    return i, time.time() - t0


def srt(pl):
    def ts(v):
        h, r = divmod(v, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"
    lines, k = [], 1
    for x in pl:
        if not x["meta"]:
            continue
        for c in x["meta"]["cues"]:
            a, b = x["voice_at"] + c["start"], x["voice_at"] + c["end"]
            lines.append(f"{k}\n{ts(a)} --> {ts(b)}\n{c['text']}\n")
            k += 1
    return "\n".join(lines)


def assemble(pl, T, out):
    lst = os.path.join(SEG, "list.txt")
    with open(lst, "w") as f:
        for i in range(len(pl)):
            f.write(f"file '{os.path.join(SEG, f'{i:03d}_' + pl[i]['sc']['id'] + '.mp4')}'\n")
    subs = os.path.join(MEDIA, "subtitles.srt")
    open(subs, "w").write(srt(pl))
    mix = os.path.join(MEDIA, "audio", "mix.wav")
    subprocess.check_call(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", mix, "-i", subs,
                           "-map", "0:v", "-map", "1:a", "-map", "2:s", "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                           "-c:s", "mov_text", "-metadata:s:s:0", "language=eng", "-metadata", "title=The Breathing Planet",
                           "-movflags", "+faststart", out])


if __name__ == "__main__":
    pl, T = P.plan()
    only = set(sys.argv[1:])
    jobs = [(i, os.path.join(SEG, f"{i:03d}_{x['sc']['id']}.mp4")) for i, x in enumerate(pl) if not only or x["sc"]["id"] in only]
    jobs.sort(key=lambda j: -pl[j[0]]["dur"])
    t0 = time.time()
    with Pool(int(os.environ.get("OCO_PROCS", "4"))) as pool:
        for i, dt_ in pool.imap_unordered(render_scene, jobs):
            print(f"[{time.time() - t0:7.0f}s] {i:3d} {pl[i]['sc']['id']:<22} {dt_:6.1f}s for {pl[i]['dur']:.1f}s", flush=True)
    if not only:
        out = os.path.join(MEDIA, "the_breathing_planet.mp4")
        assemble(pl, T, out)
        print("FINAL", out, T)
