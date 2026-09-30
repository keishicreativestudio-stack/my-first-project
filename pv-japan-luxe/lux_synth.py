"""Black-and-gold 72 BPM score for the Luxe trailer (30 s).

A low drone and a gold shimmer for the prologue; from the first image a watch tick on
every beat (tick / tock), a legato cello line and sparse high piano over
Dm9 - Bbmaj7 - Gm9 - A7sus/A7 - Dm9 - Bbmaj7 - Gm9 - A7sus, soft string pads, a quiet
air shimmer under each gold-line wipe and a chime on each title. Half a beat of
silence, then the logo lands on D major (Picardy third) with a deep hit and a
shimmer; the cello holds D to the end.
Usage: python3 lux_synth.py ../audio/synth.py ../wa/wa_synth.py cues.json out.wav
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
LOGO = C["logo"]


def piano(m, dur, vel=0.6):
    f = midi(m)
    L = dur + 1.8
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
    s *= np.clip((dur + 0.3 - t) / 0.3, 0, 1)
    s = filt(s, "lp", 1800 + 7000 * vel)
    return s * vel * 0.32


def cello(m, dur, amp=1.0, att=0.25):
    L = dur + 0.5
    t = tt(L)
    vib = 1 + 0.0045 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.35) / 0.5, 0, 1)
    ph = 2 * np.pi * np.cumsum(midi(m) * vib) / SR
    s = sum(np.sin(k * ph) / k * (0.85 ** k) for k in range(1, 22))
    s = filt(s, "lp", 2400)
    s = s + filt(s, "bp", (200, 320)) * 0.8 + filt(s, "bp", (900, 1300)) * 0.4
    bow = filt(noise(L), "bp", (1500, 5000)) * 0.03
    env = np.clip(t / att, 0, 1) ** 1.5 * np.clip((dur + 0.45 - t) / 0.45, 0, 1)
    return (s + bow) * env * amp * 0.22


def tick(amp=1.0, tock=False):
    d = 0.06
    t = tt(d)
    f = 2600 if not tock else 2100
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 160) * 0.6 + filt(noise(d), "hp", 5000) * np.exp(-t * 400)
    s += np.sin(2 * np.pi * f * 2.7 * t) * np.exp(-t * 260) * 0.25
    return s * amp * 0.35


def shimmer(amp=1.0, seed=0, top=100):
    r = np.random.default_rng(seed)
    out = np.zeros(int(2.4 * SR))
    for k in range(9):
        b = bell(top - r.integers(0, 14), 1.8, 0.2 + 0.1 * r.random())
        i = int(k * 0.06 * SR); out[i:i + len(b)] += b[:len(out) - i]
    return out * amp


def air(dur, amp=1.0):
    t = tt(dur)
    return sweep_filter(noise(dur), "bp", 2000, 7000) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2 * amp * 0.12


def drone(dur, root=26, amp=1.0):
    t = tt(dur)
    s = sum(np.sin(2 * np.pi * midi(m) * t + 0.4 * np.sin(2 * np.pi * 0.13 * t * (i + 1))) * a for i, (m, a) in enumerate(((root, 1), (root + 12, .5), (root + 19, .22))))
    return s * np.minimum(1, t / 1.2) * np.clip((dur - t) / 0.4, 0, 1) * amp * 0.12


CH = {"Dm9": (38, [53, 57, 60, 64]), "Bbmaj7": (34, [53, 57, 62, 65]), "Gm9": (43, [53, 57, 58, 62]),
      "A7sus": (45, [55, 57, 62, 64]), "A7": (45, [55, 57, 61, 64]), "D": (38, [54, 57, 62, 64, 66])}
TL = [(5, 5, "Bbmaj7"), (10, 4, "Gm9"), (14, 2, "A7sus"), (16, 2, "A7"), (18, 4, "Dm9"), (22, 4, "Bbmaj7"), (26, 2.5, "Gm9"), (28.5, 1.5, "A7sus")]

# ---------------- prologue
place(music, 0, drone(B(5) + 0.4, 26, 1.0), rev=0.3)
place(music, 0.2, pad([50, 57, 62, 64], B(5), 900, 2.0, 0.8), 0.45, rev=0.5)
place(sfx, 0.5, shimmer(0.7, 1), pan=0.1, rev=0.6)
for k, m in enumerate([74, 76, 81]):
    place(music, 1.9 + k * B(0.5), piano(m, B(1.5), 0.45), pan=0.15, rev=0.6)
place(sfx, B(5) - 1.0, reverse_swell(1.0, 0.35))

# ---------------- body
for b0, ln, name in TL:
    root, notes = CH[name]
    place(music, B(b0), pad(notes, B(ln) + 0.3, 1400, 0.6, 0.8), 0.5, rev=0.5)
    place(music, B(b0), drone(B(ln) + 0.3, root, 0.8), rev=0.2)
    place(music, B(b0), piano(root, B(ln), 0.5), pan=-0.2, rev=0.4)
    for k, m in enumerate(notes[1:] + [notes[1] + 12]):   # a slow broken chord up high
        place(music, B(b0 + 0.5 + k * 0.5), piano(m + 12, B(ln - 0.5 - k * 0.5), 0.4), pan=0.2, rev=0.55)
CEL = [(5, 57, 3), (8, 62, 2), (10, 58, 2), (12, 62, 2), (14, 64, 2), (16, 61, 2), (18, 62, 3), (21, 65, 1),
       (22, 69, 2.5), (24.5, 67, 1.5), (26, 65, 2), (28, 64, 1), (29, 61, 1)]
for b0, m, ln in CEL:
    place(music, B(b0), cello(m - 12, B(ln), 1.0 if b0 < 22 else 1.2), pan=-0.1, rev=0.45)
for bt in range(5, 30):
    place(sfx, B(bt), tick(0.8 if bt % 2 == 0 else 0.6, tock=bt % 2 == 1), pan=0.25)
for c in C["cuts"]:
    place(sfx, c - 0.47, air(0.95, 1.0), pan=0.0, rev=0.4)
    place(sfx, c, boom(1.6) * 0.18, 1.0)
for i, w in enumerate(C["words"][1:]):
    place(sfx, w, shimmer(0.35, 10 + i, 98), pan=0.15, rev=0.6)

# ---------------- logo: D major
place(sfx, LOGO, boom(3.0), 0.5); place(sfx, LOGO, crash(3.0, 0.25), rev=0.6)
place(sfx, LOGO + 0.05, shimmer(0.9, 3, 103), rev=0.7)
root, notes = CH["D"]
for k, m in enumerate([26, 38] + notes + [74, 78]):
    place(music, LOGO + k * 0.06, piano(m, DUR - LOGO, 0.55), pan=-0.3 + k * 0.07, rev=0.6)
place(music, LOGO, pad(notes, DUR - LOGO, 1500, 0.4, 2.0), 0.6, rev=0.6)
place(music, LOGO, cello(50, DUR - LOGO - 0.6, 1.2, att=0.5), pan=-0.1, rev=0.45)
place(music, LOGO, drone(DUR - LOGO, 26, 1.0), rev=0.3)
place(sfx, C["cta"], bell(93, 2.5, 0.35), pan=0.2, rev=0.6)

# ---------------- mix
ir_len = int(3.2 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 6000), filt(rng.standard_normal(ir_len), "lp", 6000)]) * np.exp(-ti * 1.8)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.5
out = music * 0.85 + sfx * 0.8 + wet
gate = np.ones(N)
gate[(tn > B(30) + 0.05) & (tn < LOGO - 0.02)] = 0.3
gate = np.convolve(gate, np.ones(480) / 480, "same")
out = np.vstack([filt(out[c], "hp", 28) * gate for c in range(2)])
out *= np.clip(tn / 0.4, 0, 1) * np.clip((DUR - tn) / 0.8, 0, 1)
out = np.tanh(out / np.abs(out).max() * 1.4)
out = out / np.abs(out).max() * 10 ** (-1.0 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
for a, b_ in [(0, B(5)), (B(5), B(18)), (B(18), B(30)), (B(30), LOGO), (LOGO, DUR)]:
    s_ = out[:, int(a * SR):int(b_ * SR)]
    print(round(a, 2), round(b_, 2), round(20 * np.log10(np.sqrt((s_ ** 2).mean()) + 1e-9), 1))
