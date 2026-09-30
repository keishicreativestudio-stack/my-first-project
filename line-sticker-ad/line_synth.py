"""128 BPM bouncy score for the せっかちな豆柴 sticker ad (15 s, 8 bars).

Ukulele-like plucked strums (Karplus-Strong), glockenspiel hook, claps,
soft kick, shaker and pizzicato bass in F major (I-V-vi-IV). Effects are
tied to the page's cue export: message pops, sticker boings, the running
dog (patter, whoosh, skid), title letter plinks, lineup sparkles, end chime.
Usage: python3 line_synth.py ../audio/synth.py cues.json out.wav
"""
import sys

import numpy as np

base_src, cues_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(base_src).read()
src = src[:src.index("# ---------------------------------------------------------------- instruments")]
src = src.replace("DUR = 13.5", "DUR = 15.0")
sys.argv = [base_src, cues_path, out_path]
exec(src)

C = cues
BEAT = 60 / C["bpm"]
BAR = BEAT * 4
T0 = C["t0"]


# ---------------------------------------------------------------- instruments
def pluck(m, dur=0.9, amp=1.0, bright=0.6, damp=0.994):
    f = midi(m)
    L = max(2, int(SR / f))
    n = int(dur * SR)
    y = np.zeros(n + L)
    exc = rng.uniform(-1, 1, L)
    y[:L] = np.convolve(exc, np.ones(3) / 3, "same") * (1 - bright) + exc * bright
    i = L
    while i < n + L:
        j = min(i + L, n + L)
        cur = y[i - L:j - L]
        prev = np.concatenate([[y[i - L - 1] if i - L - 1 >= 0 else 0], cur[:-1]])
        y[i:j] = damp * 0.5 * (cur + prev)
        i = j
    y = y[L:]
    t = np.arange(n) / SR
    return filt(y, "lp", 6000) * np.minimum(1, (dur - t) / 0.05) * amp * 0.5


def strum(notes, t0, dur, amp=1.0, down=True, bus=None):
    order = notes if down else notes[::-1]
    for i, m in enumerate(order):
        place(bus if bus is not None else music, t0 + i * 0.012, pluck(m, dur, amp * (0.9 if i else 1)), pan=-0.25 + i * 0.12, rev=0.12)


def glock(m, amp=1.0, dur=1.2):
    f = midi(m)
    t = tt(dur)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 3.5) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 9) + 0.12 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 16)
    return s * np.minimum(1, t / 0.001) * amp * 0.3


def clap(amp=1.0):
    d = 0.2
    t = tt(d)
    env = np.zeros(len(t))
    for off in (0, 0.009, 0.018):
        i = int(off * SR)
        env[i:] += np.exp(-(t[:len(t) - i]) * 60)
    return filt(noise(d), "bp", (900, 3500)) * env * amp * 0.35


def kick(amp=1.0):
    d = 0.3
    t = tt(d)
    f = 50 + 70 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11) * amp * 0.9


def shaker(amp=1.0):
    d = 0.08
    t = tt(d)
    return filt(noise(d), "bp", (5000, 10000)) * np.minimum(1, t / 0.01) * np.exp(-t * 45) * amp * 0.3


def pop_sfx(amp=1.0, pitch=1.0):
    d = 0.12
    t = tt(d)
    f = (500 + 900 * (1 - np.exp(-t * 60))) * pitch
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35) * amp * 0.5


def boing(amp=1.0, pitch=1.0):
    d = 0.35
    t = tt(d)
    f = (260 + 120 * np.sin(2 * np.pi * 14 * t) * np.exp(-t * 7) + 160 * np.exp(-t * 20)) * pitch
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * amp * 0.45


def whoosh(dur, amp=1.0, f0=600, f1=5000):
    t = tt(dur)
    return sweep_filter(noise(dur), "bp", f0, f1) * np.sin(np.pi * t / dur) ** 2 * amp * 0.5


def patter(dur, amp=1.0):
    """Quick little paw taps."""
    n = int(dur * SR)
    out = np.zeros(n)
    k = 0
    tp = 0.0
    while tp < dur - 0.03:
        i = int(tp * SR)
        tk = np.arange(int(0.03 * SR)) / SR
        f = 900 + 400 * (k % 2)
        tap = np.sin(2 * np.pi * f * tk) * np.exp(-tk * 160) + filt(rng.standard_normal(len(tk)), "bp", (1500, 4000)) * np.exp(-tk * 220) * 0.4
        e = min(n, i + len(tap))
        out[i:e] += tap[:e - i]
        tp += 0.045
        k += 1
    return out * amp * 0.35


def skid(amp=1.0):
    d = 0.22
    t = tt(d)
    squeak = np.sin(2 * np.pi * np.cumsum(2400 - 900 * t / d) / SR) * 0.3
    return (filt(noise(d), "bp", (1800, 5000)) * 0.5 + squeak) * np.sin(np.pi * t / d) * amp * 0.4


def sparkle(amp=1.0):
    d = 0.5
    t = tt(d)
    return sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 12) for f in (3520, 4186, 5274)) * amp * 0.08


# ---------------------------------------------------------------- harmony: F  C  Dm  Bb
CH = {"F": (41, [53, 57, 60, 65]), "C": (36, [52, 55, 60, 64]), "Dm": (38, [50, 57, 62, 65]), "Bb": (46, [53, 58, 62, 65])}
PROG = ["F", "C", "Dm", "Bb", "F", "C", "Bb", "C"]
HOOK = [[77, 76, 72, 69], [74, 72, 67, 72], [74, 77, 76, 72], [70, 72, 74, 77], [77, 79, 77, 72], [76, 74, 72, 67], [74, 72, 70, 72], [72, 74, 76, 79]]
kicks = []

for bar in range(8):
    t0 = bar * BAR
    root, notes = CH[PROG[bar]]
    sparse = bar == 0
    # ukulele strum pattern: D . D U . U D U
    for s8, down in ((0, True), (2, True), (3, False), (5, False), (6, True), (7, False)):
        if sparse and s8 not in (0, 2, 6):
            continue
        strum([n + 12 for n in notes], t0 + s8 * BEAT / 2, BEAT * 0.9, 0.55 if down else 0.4, down)
    # bass
    if not sparse:
        for b8, m in ((0, root), (3, root + 7), (4, root + 12), (6, root + 7)):
            place(music, t0 + b8 * BEAT / 2, pluck(m, BEAT * 0.6, 0.9, bright=0.2, damp=0.99), 0.9)
    # drums
    for beat in range(4):
        tb = t0 + beat * BEAT
        if not sparse and beat in (0, 2):
            place(music, tb, kick(0.9), 1.0)
            kicks.append(tb)
        if not sparse and beat in (1, 3):
            place(music, tb, clap(0.9), pan=0.05, rev=0.2)
        for s in range(2):
            place(music, tb + s * BEAT / 2, shaker(0.5 if s else 0.3), pan=0.35)
    # glockenspiel hook on the off-beats of beats 1-4 (sparser in the hook bar and under the lineup)
    if bar not in (0, 6):
        for i, m in enumerate(HOOK[bar]):
            place(music, t0 + i * BEAT + BEAT / 2, glock(m, 0.7), pan=-0.3, rev=0.3)

# hook bar: a little 'ta-da' under the caption and a pickup run into the title
cap = C["caption"][0]
place(sfx, cap, clap(0.9), rev=0.2)
for k, m in enumerate([72, 77]):
    place(sfx, cap + k * 0.09, glock(m, 0.8, 1.0), pan=0.1, rev=0.3)
for k, m in enumerate([72, 74, 76, 77]):
    place(music, BEAT * 3 + k * BEAT / 4, glock(m, 0.55, 0.6), pan=-0.2, rev=0.2)
place(music, BEAT * 3, pluck(41, BEAT, 0.8, bright=0.2, damp=0.99), 0.9)

# ---------------------------------------------------------------- effects
for i, tf in enumerate(C["friend"]):
    place(sfx, tf, pop_sfx(0.8, 1 + 0.05 * (i % 3)), pan=-0.35)
for i, ts in enumerate(C["sticker"]):
    place(sfx, ts, boing(0.8, 1 + 0.08 * (i % 4)), pan=0.35)
# the hook reply arrives at a sprint
first = C["sticker"][0]
place(sfx, first - 0.05, whoosh(0.3, 0.8, 3000, 800), pan=0.4)
place(sfx, first + 0.2, skid(0.8), pan=0.3)
for td in C["dash"]:
    place(sfx, td - 0.26, patter(0.42, 0.9), pan=-0.2)
    place(sfx, td - 0.24, whoosh(0.42, 0.9, 500, 6000), pan=0.0)
for i, tl in enumerate(C["letters"]):
    place(sfx, tl, glock(72 + [0, 2, 4, 7, 9, 12, 14, 16][i % 8], 0.25, 0.6), pan=-0.4 + (i % 9) * 0.1, rev=0.2)
for i, tl in enumerate(C["lineup"]):
    place(sfx, tl, pop_sfx(0.35, 1 + i * 0.04), pan=-0.5 + (i % 4) * 0.33)
place(sfx, C["lineup"][-1] + 0.1, sparkle(1.0), rev=0.4)
for tc in C["caption"]:
    place(sfx, tc, sparkle(0.5), pan=0.1, rev=0.2)
# end card: a bright chord on the downbeat, a chime on the CTA
e0 = T0["end"]
strum([65, 69, 72, 77, 81], e0, 1.6, 0.8)
for k, m in enumerate([77, 81, 84, 89]):
    place(sfx, e0 + 0.72 + k * 0.07, glock(m, 0.5, 1.4), pan=-0.2 + k * 0.15, rev=0.4)
place(sfx, DUR - BEAT * 0.5, pop_sfx(0.8, 1.3), rev=0.2)

# ---------------------------------------------------------------- mix
tn = np.arange(N) / SR
duck = np.ones(N)
for k in kicks:
    m = tn >= k
    duck[m] -= 0.2 * np.exp(-(tn[m] - k) * 10)
music *= np.clip(duck, 0.7, 1)
ir_len = int(1.4 * SR)
ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 7000), filt(rng.standard_normal(ir_len), "lp", 7000)]) * np.exp(-ti * 4)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.4
out = music * 0.7 + sfx * 0.9 + wet
out = np.vstack([filt(out[c], "hp", 40) for c in range(2)])
out *= np.clip((DUR - tn) / 0.25, 0, 1) * np.clip(tn / 0.01, 0, 1)
out = np.tanh(out / np.abs(out).max() * 1.4)
out = out / np.abs(out).max() * 10 ** (-1 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
print("peak", 20 * np.log10(np.abs(out).max()), "rms", 20 * np.log10(np.sqrt((out ** 2).mean())))
