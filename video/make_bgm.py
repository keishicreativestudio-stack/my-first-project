#!/usr/bin/env python3
"""Scene-aware background music for 『空に還る灯台』 (needs numpy).

Usage: python3 video/make_bgm.py out.wav
The timeline is taken from make_sora_video.py so section changes land on
the shot cross-fades. Each section has its own key, tempo and instruments;
neighbouring sections cross-fade.
"""
import os
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_sora_video import END_D, SHOTS, TITLE_D, XF, shot_duration  # noqa: E402

SR = 32000
RNG = np.random.default_rng(7)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a, r):
    e = np.ones(n)
    a, r = min(int(a * SR), n // 2), min(int(r * SR), n // 2)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def pad(notes, dur, bright=0.25):
    t = t_axis(dur)
    s = np.zeros_like(t)
    for m in notes:
        f = hz(m)
        for d in (-0.003, 0.0, 0.003):
            s += np.sin(2 * np.pi * f * (1 + d) * t + RNG.uniform(0, 6.28))
            s += bright * np.sin(4 * np.pi * f * (1 + d) * t)
    return s * env(len(t), 1.2, 1.5) / (len(notes) * 3)


def bell(m, dur=3.0, decay=1.3):
    t = t_axis(dur)
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t * 3) \
        + 0.15 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t * 6)
    return s * np.exp(-t / decay) * env(len(t), 0.003, 0.05)


def piano(m, dur=3.0, decay=0.9):
    t = t_axis(dur)
    f = hz(m)
    s = sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * k / decay) / k ** 1.4 for k in range(1, 7))
    return s * env(len(t), 0.004, 0.08)


def bass(m, dur):
    t = t_axis(dur)
    f = hz(m)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * env(len(t), 0.05, 0.4)


def shaped_noise(dur, lo, hi):
    n = int(dur * SR)
    spec = np.fft.rfft(RNG.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= ((fr > lo) & (fr < hi)) / np.sqrt(np.maximum(fr, 20))
    s = np.fft.irfft(spec, n)
    return s / (np.abs(s).max() + 1e-9)


def timpani(m, dur=2.5):
    t = t_axis(dur)
    f = hz(m) * (1 + 0.15 * np.exp(-t * 20))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2) * env(len(t), 0.005, 0.1)


def add(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += gain * sig


def reverb(x, secs=2.6, mix=0.35):
    n = int(secs * SR)
    ir = RNG.standard_normal(n) * np.exp(-np.arange(n) / SR * 6.9 / secs)
    ir /= np.sqrt((ir ** 2).sum())
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    wet = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return (1 - mix) * x + mix * wet


# ---- sections ---------------------------------------------------------------
# chords: list of (bass note, [pad notes]); bpm; 4 beats per chord.
SECTIONS = {
    "night":    dict(bpm=60, chords=[(45, [57, 60, 64]), (41, [53, 57, 60, 64]), (48, [55, 60, 64]), (43, [55, 59, 62])],
                     scale=[69, 72, 74, 76, 79, 81], bells=0.35),
    "workshop": dict(bpm=72, chords=[(41, [53, 57, 60]), (40, [52, 55, 60]), (38, [50, 53, 57]), (46, [50, 53, 58])],
                     arp="box"),
    "journey":  dict(bpm=96, chords=[(38, [50, 54, 57]), (45, [52, 57, 61]), (47, [50, 54, 59]), (43, [50, 55, 59])],
                     arp="piano", pulse=True, shaker=True),
    "storm":    dict(bpm=100, chords=[(38, [50, 53, 57]), (34, [50, 53, 58]), (43, [50, 55, 58]), (45, [49, 52, 57])],
                     tremolo=True, storm=True),
    "tower":    dict(bpm=56, chords=[(40, [55, 59, 66]), (36, [55, 59, 64]), (45, [55, 60, 64, 71]), (47, [54, 59, 64])],
                     scale=[71, 74, 76, 78, 83], bells=0.25, clock=True),
    "farewell": dict(bpm=58, chords=[(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (40, [56, 59, 64])],
                     melody=[76, 74, 72, 71, 72, 69, 71, 68, 69, 72, 71, 69, 67, 69, 64, 64]),
    "awaken":   dict(bpm=80, chords=[(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [60, 64, 67]), (43, [59, 62, 67])],
                     arp="box", build=True),
    "light":    dict(bpm=80, chords=[(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])],
                     arp="piano", scale=[79, 81, 84, 86, 88, 91], bells=0.6, pulse=True),
    "dawn":     dict(bpm=66, chords=[(41, [53, 57, 60]), (48, [52, 55, 60]), (38, [50, 53, 57]), (46, [50, 53, 58])],
                     arp="box", scale=[77, 79, 81, 84], bells=0.2),
}
GAIN = {"night": 0.8, "workshop": 0.85, "journey": 1.0, "storm": 1.05, "tower": 0.8,
        "farewell": 0.85, "awaken": 1.0, "light": 1.1, "dawn": 0.85}
# section of each shot, in order
SHOT_SECTIONS = ["night", "workshop", "workshop", "workshop", "journey", "journey", "journey", "journey",
                 "storm", "tower", "tower", "tower", "tower", "tower", "farewell", "farewell",
                 "awaken", "light", "light", "dawn", "dawn"]


def render_section(name, dur):
    cfg = SECTIONS[name]
    beat = 60 / cfg["bpm"]
    bar = 4 * beat
    buf = np.zeros(int(dur * SR))
    nbars = int(np.ceil(dur / bar))
    mel = cfg.get("melody")
    for b in range(nbars):
        root, notes = cfg["chords"][b % len(cfg["chords"])]
        t0 = b * bar
        lvl = 0.55 + 0.6 * (b / max(1, nbars - 1)) if cfg.get("build") else 1.0
        p = pad(notes, bar + 1.5, bright=0.15 if cfg.get("tremolo") else 0.25)
        if cfg.get("tremolo"):
            tt = t_axis(len(p) / SR)
            p = p * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * tt))
        add(buf, p, t0, 0.5 * lvl)
        add(buf, bass(root, bar + 0.3), t0, 0.25 * lvl)
        if cfg.get("pulse"):
            for k in range(4):
                add(buf, bass(root, beat * 0.6), t0 + k * beat, 0.18 * lvl)
        if cfg.get("shaker"):
            for k in range(8):
                add(buf, shaped_noise(0.06, 5000, 11000) * env(int(0.06 * SR), 0.002, 0.05), t0 + (k + 0.5) * beat / 2, 0.04)
        arp = cfg.get("arp")
        if arp:
            seq = sorted(notes) + [notes[0] + 12, sorted(notes)[1] + 12]
            seq = seq + seq[-2:0:-1]
            steps = 8 if not cfg.get("build") else (8 if b < nbars / 2 else 16)
            for k in range(steps):
                m = seq[k % len(seq)] + 12
                at = t0 + k * bar / steps
                if arp == "box":
                    add(buf, bell(m + 12, 2.0, 0.8), at, 0.16 * lvl)
                else:
                    add(buf, piano(m, 1.6, 0.6), at, 0.14 * lvl)
        if cfg.get("bells"):
            for k in range(4):
                if RNG.random() < cfg["bells"]:
                    add(buf, bell(RNG.choice(cfg["scale"]), 4.0, 1.6), t0 + k * beat, 0.13)
        if mel:
            for k in range(4):
                idx = (b * 4 + k) % len(mel)
                add(buf, piano(mel[idx], 3.5, 1.4), t0 + k * beat, 0.22)
            add(buf, piano(notes[0], 3.0, 1.2), t0, 0.1)
        if cfg.get("clock"):
            for k in range(4):
                add(buf, shaped_noise(0.03, 2000, 6000) * env(int(0.03 * SR), 0.001, 0.025), t0 + k * beat, 0.05)
        if cfg.get("storm") and b % 2 == 0:
            add(buf, timpani(root - 12), t0, 0.5)
        if cfg.get("build") and b >= nbars - 2:
            for k in range(16):
                add(buf, timpani(33, 0.5), t0 + k * bar / 16, 0.12 + 0.02 * k)
    if cfg.get("storm"):
        add(buf, shaped_noise(dur, 25, 350) * env(int(dur * SR), 2.5, 3.0), 0, 0.35)
        at = 2.0
        while at < dur - 3:
            crack = shaped_noise(2.5, 30, 2500) * np.exp(-t_axis(2.5) * 2.5) * env(int(2.5 * SR), 0.01, 0.1)
            add(buf, crack, at, 0.45)
            at += RNG.uniform(5.5, 9.0)
    return reverb(buf, 3.2 if name in ("tower", "farewell", "dawn") else 2.4)


def timeline():
    """[(section, start, end)] with boundaries at the middle of each shot cross-fade."""
    starts, t = [], TITLE_D - XF
    for s in SHOTS:
        starts.append(t)
        t += shot_duration(s[6]) - XF
    total = t + END_D
    spans = []
    for i, name in enumerate(SHOT_SECTIONS):
        a = 0.0 if i == 0 else starts[i] + XF / 2
        b = total if i == len(SHOTS) - 1 else starts[i + 1] + XF / 2
        if spans and spans[-1][0] == name:
            spans[-1] = (name, spans[-1][1], b)
        else:
            spans.append((name, a, b))
    return spans, total


def main(out):
    assert len(SHOT_SECTIONS) == len(SHOTS)
    spans, total = timeline()
    mix = np.zeros((int(total * SR) + SR, 2))
    X = 2.0  # section cross-fade
    for i, (name, a, b) in enumerate(spans):
        a0, b0 = max(0.0, a - X / 2), min(total, b + X / 2)
        dur = b0 - a0
        left = render_section(name, dur)
        right = np.roll(left, int(0.012 * SR))  # slight width
        e = env(len(left), X if i else 3.0, X if i < len(spans) - 1 else 6.0)
        seg = np.stack([left * e, right * e], axis=1) * GAIN[name]
        i0 = int(a0 * SR)
        mix[i0:i0 + len(seg)] += seg[: len(mix) - i0]
        print(f"{name:9s} {a:6.1f}–{b:6.1f}s")
    mix = mix[: int(total * SR)]
    mix *= 0.5 / (np.abs(mix).max() + 1e-9)  # peak at -6 dBFS
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    print(f"wrote {out} ({total:.1f}s)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bgm.wav")
