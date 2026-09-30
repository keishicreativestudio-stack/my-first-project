"""Warm 100 BPM acoustic score for the 旅のノート trailer (30 s).

Karplus-Strong acoustic guitar strumming C G Am F with a stomp / clap / shaker groove,
an upright-ish bass, a whistled melody and a glockenspiel doubling it in the fast
stretch. Bars start one beat in (the pickup strum at 0). A soft pen scribble follows the
red route on every leg, a paper slap and tape rip on every polaroid, a page turn when
the window becomes the first photo, a flurry as the twelve prints gather, then a
breakdown under the Earth and a last ringing C chord with a bell on the call to action.
Usage: python3 journal_synth.py ../audio/synth.py ../wa/wa_synth.py cues.json out.wav
"""
import sys
import numpy as np

base, wa_path, cues_path, out_path = sys.argv[1:5]
src = open(base).read()
src = src[:src.index("# ---------------------------------------------------------------- arrangement")].replace("DUR = 13.5", "DUR = 30.0")
sys.argv = [base, cues_path, out_path]
exec(src)
wa = open(wa_path).read()
exec(wa[wa.index("\n# ---------------------------------------------------------------- instruments"):wa.index("\n# ---------------------------------------------------------------- arrangement")])

C = cues
BEAT = 60 / C["bpm"]; BAR = BEAT * 4; E8 = BEAT / 2
O = C["origin"]                      # bar grid starts one beat in
B = lambda b: b * BEAT
at = lambda bar, beat=0: O + bar * BAR + beat * BEAT
tn = np.arange(N) / SR
r_ = np.random.default_rng(3)


def ks(f, dur, bright=0.5, amp=1.0):
    n = int(dur * SR); p = max(2, int(SR / f))
    buf = r_.uniform(-1, 1, p) * amp
    buf = filt(np.concatenate([buf, buf]), "lp", 1500 + 6000 * bright)[:p]
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.4985 * (buf[i % p] + buf[(i + 1) % p])
    return out


def string_cache():
    cache = {}
    def get(m, dur):
        k = (m, round(dur, 2))
        if k not in cache: cache[k] = ks(midi(m), dur, 0.55)
        return cache[k]
    return get
S_ = string_cache()


def strum(notes, dur, down=True, amp=1.0):
    order = notes if down else notes[::-1]
    out = np.zeros(int((dur + 0.1) * SR))
    for k, m in enumerate(order):
        s = S_(m, dur) * (0.8 if not down else 1.0)
        i = int(k * 0.011 * SR); out[i:i + len(s)] += s[:len(out) - i]
    t = np.arange(len(out)) / SR
    return out * np.clip((dur + 0.08 - t) / 0.08, 0, 1) * amp * 0.28


def whistle(m, dur, amp=1.0, slide_from=None):
    t = tt(dur + 0.05)
    f0 = midi(m) * np.ones(len(t))
    if slide_from is not None: f0 = midi(m) + (midi(slide_from) - midi(m)) * np.exp(-t * 30)
    f = f0 * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.12) / 0.2, 0, 1))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.04 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    s += filt(noise(dur + 0.05), "bp", (midi(m) * 0.9, midi(m) * 1.1)) * 0.08
    env = np.clip(t / 0.03, 0, 1) * np.clip((dur + 0.05 - t) / 0.06, 0, 1)
    return s * env * amp * 0.22


def glock(m, amp=1.0):
    return bell(m + 12, 1.0, amp * 0.5)


def stomp(amp=1.0):
    d = 0.35
    t = tt(d)
    body = np.sin(2 * np.pi * (55 + 70 * np.exp(-t * 30)) * t) * np.exp(-t * 11)
    wood = filt(noise(d), "bp", (150, 900)) * np.exp(-t * 35) * 0.6
    return np.tanh((body + wood) * 1.4) * amp * 0.9


def clap(amp=1.0):
    d = 0.25
    t = tt(d)
    env = np.zeros(len(t))
    for off in (0, 0.012, 0.025):
        i = int(off * SR); env[i:] += np.exp(-t[:len(t) - i] * 32)
    return filt(noise(d), "bp", (900, 5000)) * env * amp * 0.42


def shaker(amp=1.0):
    d = 0.09
    t = tt(d)
    return filt(noise(d), "bp", (4500, 11000)) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * amp * 0.28


def ubass(m, dur, amp=1.0):
    t = tt(dur)
    f = midi(m)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.1 * np.sin(6 * np.pi * f * t)
    return s * np.minimum(1, t / 0.005) * np.exp(-t * 2.5) * np.clip((dur - t) / 0.03, 0, 1) * amp * 0.55


def scribble(dur, amp=1.0):
    t = tt(dur)
    am = 0.5 + 0.5 * np.sin(2 * np.pi * (7 + 3 * np.sin(2 * np.pi * 0.9 * t)) * t) ** 2
    return filt(noise(dur), "bp", (2500, 7000)) * am * np.sin(np.pi * np.clip(t / dur, 0, 1)) * amp * 0.16


def slap(amp=1.0):
    d = 0.25
    t = tt(d)
    thud = filt(noise(d), "lp", 700) * np.exp(-t * 40)
    snap_ = filt(noise(d), "bp", (1500, 6000)) * np.exp(-t * 90) * 0.6
    rip = filt(noise(d), "bp", (3000, 9000)) * np.clip((t - 0.06) / 0.02, 0, 1) * np.exp(-np.maximum(t - 0.06, 0) * 25) * 0.35
    return (thud + snap_ + rip) * amp * 0.8


def page(amp=1.0):
    d = 0.5
    t = tt(d)
    return sweep_filter(noise(d), "bp", 600, 5000) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5 * amp * 0.4


CH = {"C": (36, [48, 52, 55, 60, 64]), "G": (31, [43, 47, 50, 55, 59, 67]), "Am": (33, [45, 52, 57, 60, 64]), "F": (29, [41, 48, 53, 57, 60, 65])}
PROG = ["C", "G", "Am", "F"]
MEL = {"C": [(0, 76, 1), (1, 79, 1), (2, 84, 2), (4, 83, 1), (5, 79, 1), (6, 76, 2)],
       "G": [(0, 74, 1), (1, 79, 1), (2, 83, 2), (4, 81, 1), (5, 79, 1), (6, 74, 2)],
       "Am": [(0, 72, 1), (1, 76, 1), (2, 81, 2), (4, 79, 1), (5, 76, 1), (6, 72, 2)],
       "F": [(0, 72, 1), (1, 74, 1), (2, 77, 2), (4, 76, 1), (5, 74, 1), (6, 79, 2)]}
PATTERN = [(0, True), (1, True), (1.5, False), (2.5, False), (3, True), (3.5, False)]   # D D U . U D U


def bar(b, name, drums=1, whistle_on=1.0, glock_on=0.0, strum_amp=1.0, shake16=False, claps=True):
    root, notes = CH[name]
    for bt, down in PATTERN:
        place(music, at(b, bt), strum(notes, BEAT * (0.5 if bt % 1 else 1.0) * 1.05, down, strum_amp), pan=-0.15, rev=0.2)
    place(music, at(b, 0), ubass(root, BEAT * 1.8), 1.0); place(music, at(b, 2), ubass(root + 7 if name != "F" else root + 7, BEAT * 1.8, 0.9), 1.0)
    if drums:
        for q in (0, 2): place(music, at(b, q), stomp(1.0), 1.0, rev=0.1)
        place(music, at(b, 2.5), stomp(0.5), 1.0)
        if claps:
            for q in (1, 3): place(music, at(b, q), clap(0.9), pan=0.05, rev=0.25)
        for e in range(16 if shake16 else 8):
            place(music, at(b, e * (0.25 if shake16 else 0.5)), shaker(0.8 if e % 2 == 0 else 0.5), pan=0.3)
    for e, m, ln in MEL[name]:
        if whistle_on: place(music, at(b, e / 2), whistle(m, E8 * ln * 0.95, whistle_on, slide_from=m - 2 if e == 0 else None), pan=0.1, rev=0.35)
        if glock_on: place(music, at(b, e / 2), glock(m, glock_on), pan=-0.25, rev=0.3)


# ---------------- pickup and intro (the window)
place(music, 0.0, strum(CH["G"][1], BEAT * 1.0, True, 0.8), rev=0.3)
place(music, E8, whistle(79, E8 * 0.9, 0.8, slide_from=74), rev=0.4)
bar(0, "C", drums=0, whistle_on=0.8)                           # beats 1-5 (window -> Kyoto)
place(sfx, C["shrink"] - 0.1, page(1.0), rev=0.2)
# ---------------- slow legs: bars 1-3
for b in range(1, 4): bar(b, PROG[b % 4], drums=1, whistle_on=0.9, claps=b >= 2)
# ---------------- fast legs: bars 4-7
for b in range(4, 8): bar(b, PROG[b % 4], drums=1, whistle_on=1.0, glock_on=0.7, shake16=True)
# ---------------- bar 8 (beats 33-37): Machu Picchu hold, build with a stomp fill
bar(8, "G", drums=1, whistle_on=0.0, glock_on=0.0)
for k in range(4): place(music, at(8, 3 + k * 0.25), stomp(0.5 + 0.15 * k), 1.0)
place(sfx, at(8, 2), reverse_swell(BEAT * 2, 0.5))
# ---------------- grid (bar 9) - everything at once
bar(9, "C", drums=1, whistle_on=1.1, glock_on=0.9, shake16=True)
place(sfx, C["grid"], crash(2.0, 0.6), rev=0.4)
for i in range(12): place(sfx, C["grid"] + i * 0.06, slap(0.35), pan=-0.4 + i * 0.07)
# ---------------- earth (bar 10): breakdown
root, notes = CH["F"]
place(music, at(10), strum(notes, BAR * 0.95, True, 0.9), rev=0.5)
place(music, at(10, 2), strum(CH["G"][1], BEAT * 2, True, 0.8), rev=0.5)
place(music, at(10), pad([53, 57, 60, 65], BAR, 1600, 0.5, 0.8), 0.45, rev=0.5)
for e, m, ln in [(0, 81, 3), (4, 79, 2), (6, 77, 2)]: place(music, at(10, e / 2), whistle(m, E8 * ln, 0.9), rev=0.5)
# ---------------- logo (bar 11 +): final C
fin = at(11)
for k, (m, a) in enumerate([(36, 1.0), (48, 1.0)]): place(music, fin, ubass(m, 2.6, 0.9), 1.0)
place(music, fin, strum(CH["C"][1] + [67, 72], 2.8, True, 1.1), rev=0.6)
place(music, fin, pad([48, 55, 60, 64, 67], DUR - fin, 1500, 0.3, 1.5), 0.5, rev=0.6)
place(music, fin, whistle(84, 1.6, 1.0, slide_from=79), rev=0.6)
place(sfx, fin, crash(2.5, 0.35), rev=0.5)
place(sfx, C["name"], bell(96, 2.0, 0.35), pan=0.2, rev=0.6)
place(sfx, C["cta"], bell(91, 2.0, 0.45), pan=-0.1, rev=0.6)

# ---------------- route sfx
for a, b_ in C["legs"]: place(sfx, a, scribble(b_ - a, 1.0), pan=0.2)
for i, ta in enumerate(C["arrivals"]): place(sfx, ta, slap(0.9), pan=(-0.25 if i % 2 else 0.25), rev=0.15)

# ---------------- mix
ir_len = int(1.8 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 6500), filt(rng.standard_normal(ir_len), "lp", 6500)]) * np.exp(-ti * 3)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.4
out = music * 0.85 + sfx * 0.75 + wet
out = np.vstack([filt(out[c], "hp", 35) for c in range(2)])
out *= np.clip(tn / 0.05, 0, 1) * np.clip((DUR - tn) / 0.8, 0, 1)
out = np.tanh(out / np.abs(out).max() * 1.9)
out = out / np.abs(out).max() * 10 ** (-0.8 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
for a, b_ in [(0, at(1)), (at(1), at(4)), (at(4), at(8)), (at(8), at(9)), (at(9), at(10)), (at(10), at(11)), (at(11), DUR)]:
    s_ = out[:, int(a * SR):int(b_ * SR)]
    print(round(a, 2), round(b_, 2), round(20 * np.log10(np.sqrt((s_ ** 2).mean()) + 1e-9), 1))
