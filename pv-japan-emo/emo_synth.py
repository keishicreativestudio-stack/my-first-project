"""Nostalgic 80 BPM piano score for the 365日 trailer (30 s).

A felt-soft piano on the royal-road progression in D (IV V iii vi), vinyl crackle and a
faint projector flutter under everything. Strings creep in with the festival, soft
kick / rim / shaker from beat 16, 8th-note arpeggios while the prints pile up (a camera
shutter on each print), one held breath, then the climax on D as the last shot opens.
The logo is piano alone, ending on a rolled Dadd9 and a small bell on the call to action.
Usage: python3 emo_synth.py ../audio/synth.py ../wa/wa_synth.py cues.json out.wav
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
BEAT = 60 / C["bpm"]
B = lambda b: b * BEAT
tn = np.arange(N) / SR


def piano(m, dur, vel=0.6):
    f = midi(m)
    L = dur + 1.6
    t = tt(L)
    hi = (f / 262) ** 0.45
    out = np.zeros(len(t))
    for n in range(1, 16):
        fn = n * f * np.sqrt(1 + 0.00035 * n * n)
        if fn > 15000: break
        a = (1 / n) ** (1.9 - 0.8 * vel)
        dec = 0.7 * np.exp(-t * (1.1 + 0.45 * n) * hi) + 0.3 * np.exp(-t * (0.22 + 0.07 * n) * hi)
        for det in (-0.0007, 0.0007):
            out += np.sin(2 * np.pi * fn * (1 + det) * t + n) * a * dec * 0.5
    ham = filt(noise(L), "bp", (min(f * 2, 4000), min(f * 9, 12000))) * np.exp(-t * 140) * 0.25 * vel
    s = (out + ham) * np.minimum(1, t / 0.002)
    s *= np.clip((dur + 0.3 - t) / 0.3, 0, 1)   # damper
    s = filt(s, "lp", 1800 + 7000 * vel)
    return s * vel * 0.32


def shutter(amp=1.0):
    d = 0.35
    t = tt(d)
    out = np.zeros(len(t))
    for st, a in ((0, 1), (0.055, 0.7)):
        i = int(st * SR); u = t[:len(t) - i]
        out[i:] += filt(noise(d - st), "bp", (1500, 9000)) * np.exp(-u * 260) * a
        out[i:] += np.sin(2 * np.pi * 900 * u) * np.exp(-u * 120) * a * 0.3
    wind = filt(noise(d), "bp", (500, 2500)) * np.clip((t - 0.1) / 0.05, 0, 1) * np.clip((0.3 - t) / 0.05, 0, 1) * 0.15
    return (out + wind) * amp * 0.5


def paper(amp=1.0):
    d = 0.2
    t = tt(d)
    return (filt(noise(d), "lp", 900) * np.exp(-t * 40) + filt(noise(d), "bp", (2000, 6000)) * np.exp(-t * 60) * 0.3) * amp * 0.6


def rim(amp=1.0):
    d = 0.12
    t = tt(d)
    return (np.sin(2 * np.pi * 1650 * t) * np.exp(-t * 90) * 0.6 + filt(noise(d), "bp", (2000, 6000)) * np.exp(-t * 110)) * amp * 0.35


def shaker(amp=1.0):
    d = 0.09
    t = tt(d)
    return filt(noise(d), "hp", 6000) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * amp * 0.3


def soft_kick(amp=1.0):
    return filt(kick(amp, 0.45, 42, 110), "lp", 900)


# ---------------- chords (beats) in D
CH = {"Gmaj7": (43, [55, 59, 62, 66]), "A": (45, [57, 61, 64, 69]), "F#m7": (42, [54, 57, 61, 64]),
      "Bm7": (47, [57, 59, 62, 66]), "Em7": (40, [55, 59, 62, 64]), "A7sus": (45, [55, 57, 62, 64]),
      "D": (38, [57, 62, 64, 66, 69]), "Dadd9": (38, [62, 66, 69, 74, 76, 78])}
TL = [(0, 4, "Gmaj7"), (4, 4, "A"), (8, 4, "F#m7"), (12, 4, "Bm7"), (16, 4, "Gmaj7"), (20, 2, "A"), (22, 2, "F#m7"),
      (24, 2, "Bm7"), (26, 1, "Em7"), (27, 1, "A7sus"), (28, 4, "D"), (32, 2, "Gmaj7"), (34, 2, "Em7"), (36, 4, "Dadd9")]

for b0, ln, name in TL:
    root, notes = CH[name]
    vel = 0.45 if b0 < 16 else 0.55 if b0 < 21 else 0.62 if b0 < 28 else 0.8 if b0 < 34 else 0.45
    if name == "A7sus":   # the held breath: one soft high note only
        place(music, B(b0), piano(88, B(1.2), 0.3), pan=0.2, rev=0.7)
        continue
    if name == "Dadd9":   # rolled final chord
        for k, m in enumerate([38, 50] + notes):
            place(music, B(b0) + k * 0.07, piano(m, B(4) - k * 0.07, 0.5), pan=-0.3 + k * 0.08, rev=0.6)
        continue
    place(music, B(b0), piano(root, B(ln), vel), pan=-0.15, rev=0.4)
    if b0 < 8 or b0 >= 34:            # sparse: a chord on the downbeat
        for m in notes: place(music, B(b0) + 0.02, piano(m, B(ln) * 0.9, vel * 0.55), pan=0.05, rev=0.5)
    elif b0 < 21:                     # broken chord in 8ths
        pat = [root + 12, notes[1], notes[2], notes[3], notes[2], notes[1], notes[2], notes[3]]
        for e in range(int(ln * 2)):
            place(music, B(b0) + e * B(0.5), piano(pat[e % 8], B(0.5) * 1.6, vel * 0.55), pan=-0.1, rev=0.45)
    else:                             # montage + climax: 8ths plus chord stabs on the beat
        pat = [root + 12, notes[1], notes[2], notes[-1], notes[2], notes[1]]
        for e in range(int(ln * 2)):
            place(music, B(b0) + e * B(0.5), piano(pat[e % 6], B(0.5) * 1.3, vel * 0.55), pan=-0.1, rev=0.45)
        for q in range(ln):
            for m in notes[1:]: place(music, B(b0 + q), piano(m + 12, B(0.9), vel * 0.35), pan=0.15, rev=0.5)
        if b0 >= 28: place(music, B(b0), piano(root - 12, B(ln), 0.7), rev=0.3)

MEL = [(1, 78, 1), (2, 76, 1), (3, 74, 1), (4, 76, 1.5), (5.5, 73, .5), (6, 69, 2),
       (8, 73, 1), (9, 76, 1), (10, 81, 1.5), (11.5, 78, .5), (12, 78, 1.5), (13.5, 76, .5), (14, 74, 2),
       (16, 78, .5), (16.5, 79, .5), (17, 81, 1.5), (18.5, 83, .5), (19, 81, 1), (20, 81, 1), (21, 79, .5), (21.5, 78, .5),
       (22, 76, 1), (23, 78, 1), (24, 81, 1), (25, 78, 1), (26, 79, .5), (26.5, 81, .5),
       (28, 86, 1.5), (29.5, 85, .5), (30, 81, 1), (31, 78, 1), (32, 79, 1), (33, 83, 1), (34, 81, 2)]
for b0, m, ln in MEL:
    vel = 0.55 if b0 < 16 else 0.65 if b0 < 28 else 0.9 if b0 < 34 else 0.5
    place(music, B(b0), piano(m, B(ln), vel), pan=0.1, rev=0.5)
    if 28 <= b0 < 34: place(music, B(b0), piano(m - 12, B(ln), vel * 0.6), pan=0.05, rev=0.5)

# ---------------- strings
place(music, B(16), pad([55, 62, 66, 71], B(5), 1400, 2.5, 1.0), 0.5, rev=0.5)
place(music, B(21), pad([57, 62, 66, 69], B(6), 1800, 1.5, 1.0) * np.linspace(0.5, 1.1, int(B(6) * SR)), 0.6, rev=0.5)
place(music, B(28), pad([50, 57, 62, 66, 69, 74], B(6.5), 2600, 0.3, 2.0), 0.85, rev=0.5)
place(music, B(34), pad([52, 59, 62, 67], B(2.2), 1500, 0.4, 1.2), 0.35, rev=0.6)
place(music, B(36), pad([50, 57, 62, 66, 69], B(4), 1600, 0.6, 1.5), 0.35, rev=0.6)

# ---------------- drums: beats 16-27 soft, 28-34 fuller
for bt in range(16, 34):
    if bt == 27: continue
    tb = B(bt); strong = bt >= 28
    if bt % 2 == 0: place(music, tb, soft_kick(0.7 if not strong else 0.9), rev=0.1)
    if bt % 2 == 1: place(music, tb + B(0.5), soft_kick(0.45), rev=0.1)
    if bt % 2 == 1: place(music, tb, rim(0.8) if not strong else snare(0.35), pan=0.1, rev=0.3)
    for s in range(4 if bt >= 21 else 2):
        place(music, tb + s * B(1 / (4 if bt >= 21 else 2)), shaker(0.8 if s % 2 == 0 else 0.5), pan=0.35)
place(sfx, B(28), crash(3.0, 0.5), rev=0.5); place(sfx, B(28), boom(2.5), 0.35)
place(sfx, B(27), reverse_swell(B(1), 0.55))
place(sfx, B(21) - 0.1, crash(2.0, 0.25), rev=0.5)

# ---------------- sfx: shutters on each print, air on each cut, a bell on the call to action
for i, p in enumerate(C["prints"]):
    place(sfx, p, shutter(0.8), pan=(-0.2 if i % 2 else 0.2), rev=0.2)
    place(sfx, p + 0.36, paper(0.6), pan=0.0, rev=0.15)
for c in C["cuts"]:
    sw = reverse_swell(0.55, 1.0); sw = np.vstack([filt(filt(sw[k], 'lp', 2600), 'hp', 300) for k in range(2)])
    place(sfx, c - 0.5, sw * 0.5, rev=0.4)
place(sfx, C["cta"], bell(93, 2.5, 0.35), pan=0.2, rev=0.6)

# ---------------- mix
ir_len = int(3.0 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 5000), filt(rng.standard_normal(ir_len), "lp", 5000)]) * np.exp(-ti * 2.0)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.45
lift = np.interp(tn, [0, B(15), B(17), B(34), B(35)], [1.5, 1.5, 1.0, 1.0, 1.3])
out = (music * 0.85 + wet) * lift + sfx * 0.8
# vinyl: hiss, crackle, and a faint 24 fps projector flutter until the logo
hiss = filt(rng.standard_normal(N), "bp", (1500, 8000)) * 0.004
crk = np.zeros(N); idx = rng.choice(N, 420, replace=False); crk[idx] = rng.standard_normal(420) * 0.12
crk = filt(crk, "bp", (800, 7000))
proj = filt(rng.standard_normal(N), "bp", (300, 1800)) * (0.6 + 0.4 * np.sin(2 * np.pi * 24 * tn)) * 0.0022
proj *= np.clip((C["logo"] - tn) / 1.0, 0, 1)
out += np.vstack([hiss + crk + proj, hiss * 0.9 + crk + proj])
gate = np.ones(N)
gate[(tn > B(27) + 0.05) & (tn < B(28) - 0.02)] = 0.55
gate = np.convolve(gate, np.ones(480) / 480, "same")
out = np.vstack([filt(out[c], "hp", 30) * gate for c in range(2)])
out *= np.clip(tn / 0.3, 0, 1) * np.clip((DUR - tn) / 0.8, 0, 1)
out = np.tanh(out / np.abs(out).max() * 1.5)
out = out / np.abs(out).max() * 10 ** (-1.0 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
for a, b_ in [(0, B(16)), (B(16), B(21)), (B(21), B(27)), (B(27), B(28)), (B(28), B(34)), (B(34), DUR)]:
    s_ = out[:, int(a * SR):int(b_ * SR)]
    print(round(a, 2), round(b_, 2), round(20 * np.log10(np.sqrt((s_ ** 2).mean()) + 1e-9), 1))
