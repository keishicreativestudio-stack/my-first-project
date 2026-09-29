"""Soundtrack for the 30s vertical PV, driven by the page's CUES export.

Reuses the oscillator/noise instruments from the intro soundtrack (synth.py).
Usage: python3 pv_synth.py ../audio/synth.py cues.json out.wav
"""
import sys

import numpy as np

base_src, cues_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(base_src).read()
src = src[:src.index("# ---------------------------------------------------------------- arrangement")]
src = src.replace("DUR = 13.5", "DUR = 30.0")
sys.argv = [base_src, cues_path, out_path]
exec(src)  # defines SR, N, buses, place(), instruments, cues

hits = np.zeros((2, N))
BEAT = 0.5


# ---------------------------------------------------------------- extra instruments
def braam(dur=2.6):
    t = tt(dur)
    s = sum(saw(midi(m), dur, detune=d, maxf=2500) for m, d in ((26, 0), (38, -9), (38, 9), (45, 0)))
    s = sweep_filter(s, "lp", 180, 1100)
    e = np.minimum(1, t / 0.03) * np.exp(-t * 1.3)
    return np.tanh(s * 1.8) * e * 0.7


def shutter(amp=1.0):
    d = 0.05
    t = tt(d)
    return (filt(noise(d), "bp", (1500, 6000)) * np.exp(-t * 160) + np.sin(2 * np.pi * 140 * t) * np.exp(-t * 90) * 0.4) * amp


def pop(pitch=1.0, amp=1.0):
    d = 0.14
    t = tt(d)
    f = (380 + 700 * np.exp(-t * 40)) * pitch
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * amp


def paper_flip(amp=1.0):
    d = 0.16
    t = tt(d)
    return sweep_filter(noise(d), "bp", 1800, 7000) * np.sin(np.pi * t / d) * amp


def projector(dur):
    t = tt(dur)
    gate = (np.sin(2 * np.pi * 18 * t) > 0.6).astype(float)
    gate = np.convolve(gate, np.ones(40) / 40, "same")
    rattle = filt(noise(dur), "bp", (900, 4000)) * gate * 0.6
    hum = np.sin(2 * np.pi * 60 * t) * 0.12
    return (rattle + hum) * np.minimum(1, t / 0.05) * np.minimum(1, (dur - t) / 0.1)


def whoosh(dur, f0=400, f1=5000, amp=1.0):
    t = tt(dur)
    return sweep_filter(noise(dur), "bp", f0, f1) * np.sin(np.pi * t / dur) ** 2 * amp


# ---------------------------------------------------------------- arrangement
C = cues
kick_times = []

# hook: keyboard only, then the first hit
for k in C["keys"]:
    place(sfx, k, key_click(0.6 if k < 28 else 0.32), pan=rng.uniform(-0.12, 0.12))
place(sfx, 3.3, reverse_swell(0.7, 0.7))
place(sfx, 3.2, riser(0.8, 300, 4000, 0.3))
for e in C["enters"]:
    place(sfx, e, key_click(0.8, heavy=True), pan=0.05)
H1, H2 = C["hits"]
place(hits, H1, kick(1.3), 1.1)
place(hits, H1, boom(2.0), 0.9)
place(hits, H1, crash(1.2, 0.5), rev=0.3)
kick_times.append(H1)
place(sfx, H1 + 0.05, whoosh(0.6, 3000, 600, 0.6), pan=-0.2, rev=0.2)          # burst out
place(sfx, H1 + 0.4, riser(C["land"] - H1 - 0.42, 300, 6000, 0.55), rev=0.25)   # swirl in
place(hits, C["land"], kick(0.7, dur=0.6, low=50, high=120), 0.8)
for m, dt in ((74, 0), (81, 0.06)):
    place(sfx, C["land"] + dt, bell(m, 2.0), 0.3, rev=0.5)
place(sfx, 3.0, beep(2600, 0.06, 0.25), pan=0.5)
place(music, H1, pad([50, 57, 62, 65], 3.2, cutoff=900, attack=0.8, release=0.6), 0.6, rev=0.4)

# split section: four segments of three beats each
split0 = 4.0
seg_chords = [([50, 57, 62, 65], 38), ([46, 53, 62, 65], 34), ([41, 53, 57, 65], 41), ([48, 55, 60, 64], 36)]
arp_sets = [[62, 65, 69, 74], [62, 65, 70, 74], [65, 69, 72, 77], [60, 64, 67, 72]]
for k, (notes, root) in enumerate(seg_chords):
    t0 = split0 + k * 1.5
    place(music, t0, pad(notes, 1.9, cutoff=1500, attack=0.05, release=0.4), 0.45, rev=0.3)
    for i in range(12):  # 16ths
        t = t0 + i * BEAT / 4
        if i % 4 == 0:
            place(music, t, kick(0.95), 1.0)
            kick_times.append(t)
        if i % 4 == 2:
            place(music, t, hat(0.4), pan=0.25)
            place(music, t, bass(root + 12, BEAT / 2 * 0.9), 0.55)
        if i % 4 == 0:
            place(music, t, bass(root, BEAT / 2 * 0.9), 0.55)
        place(music, t, pluck(arp_sets[k][i % 4], 0.35, bright=1.1), 0.16, pan=(-.35 if i % 2 else .35), rev=0.2)
    place(sfx, t0 + 0.5, whoosh(0.35, 600, 4000, 0.35), rev=0.15)
for t in C["flips"]:
    place(sfx, t, paper_flip(0.5), pan=rng.uniform(-0.4, 0.4))
for a, z in C["rise"]:
    place(sfx, a, riser(z - a, 400, 5000, 0.35), rev=0.3)
    place(sfx, z - 0.05, bell(86, 1.2), 0.12, rev=0.5)
for i, t in enumerate(C["pops"]):
    place(sfx, t, pop(1 + i * 0.07, 0.5), pan=-0.5 + (i % 4) * 0.33)
for a, z in C["projector"]:
    place(sfx, a, projector(z - a), 0.5, pan=0.15)

# pause: groove stops, one sentence, a light sweep
p0, p1 = C["pause"]
place(music, p0, pad([46, 53, 57, 62, 69], p1 - p0 + 0.4, cutoff=1300, attack=0.9, release=0.8), 0.7, rev=0.5)
place(music, p0, boom(3.0), 0.25)
for i in range(14):
    t = 11.0 + i * 0.14
    place(sfx, t, pluck([81, 84, 86, 88, 91][i % 5], 0.5, bright=2.0), 0.07, pan=-0.6 + i * 0.09, rev=0.6)
place(sfx, 13.3, reverse_swell(0.7, 0.8))

# montage: groove returns, shutter per cut, build to the second hit
m0 = p1
for i in range(int((H2 - m0) / BEAT * 4)):
    t = m0 + i * BEAT / 4
    beat, sub = divmod(i, 4)
    if t >= H2 - 0.1:
        break
    chord = [([50, 57, 62, 65], 38), ([46, 53, 62, 65], 34), ([48, 55, 60, 64], 36), ([45, 52, 57, 61], 33)][(beat // 4) % 4]
    if sub == 0:
        place(music, t, kick(1.0), 1.0)
        kick_times.append(t)
        if beat % 4 == 0:
            place(music, t, pad(chord[0], 2.1, cutoff=2000, attack=0.05, release=0.3), 0.4, rev=0.3)
        if beat % 2 == 1:
            place(music, t, snare(0.75), rev=0.2)
    place(music, t, hat(0.28 if sub % 2 else 0.18), pan=0.2)
    if sub in (0, 2):
        place(music, t, bass(chord[1] + (12 if sub == 2 else 0), BEAT / 2 * 0.9), 0.55)
    place(music, t, pluck(chord[0][i % 4] + 12, 0.3, bright=1.5), 0.14, pan=(-.4 if i % 2 else .4), rev=0.2)
for c in C["cuts"]:
    if c["d"] >= 0.12:
        place(sfx, c["t"], shutter(0.35), pan=0.3)
place(sfx, 18.0, riser(3.9, 200, 11000, 0.8), rev=0.3)
place(sfx, 21.2, reverse_swell(0.7, 1.0))
t = 20.0
while t < H2 - 0.1:
    place(music, t, snare(0.25 + 0.6 * (t - 20) / 1.9), rev=0.15)
    t += max(0.035, 0.125 * (1 - (t - 20) / 2.2))

# second hit, mosaic, logo
place(hits, H2, kick(1.5), 1.2)
place(hits, H2, boom(3.0), 1.1)
place(hits, H2, braam(2.8), 0.9, rev=0.4)
place(hits, H2, crash(2.6, 1.0), rev=0.6)
kick_times.append(H2)
for i in range(18):
    tb = H2 + 0.6 + i * 0.045
    place(sfx, tb, beep(1800 + (i * 7 % 9) * 260, 0.035, 0.12), pan=-0.7 + (i % 8) * 0.2)
place(sfx, H2 + 1.35, whoosh(0.75, 5000, 500, 0.4), rev=0.3)
L0 = C["logo"]
place(hits, L0, kick(0.8, dur=0.8, low=36, high=90), 0.8)
for m, dt, p in ((62, 0, -0.2), (69, 0.09, 0.25), (74, 0.18, 0.0)):
    place(sfx, L0 + dt, bell(m, 2.8), 0.35, pan=p, rev=0.6)
place(music, L0, pad([50, 57, 62, 64, 69], C["end"] - L0 + 0.2, cutoff=1800, attack=0.4, release=0.3), 0.55, rev=0.5)
kick_times.append(L0)
place(sfx, 28.95, whoosh(0.4, 800, 3000, 0.25))

# ---------------------------------------------------------------- mix
duck = np.ones(N)
tn = np.arange(N) / SR
for k in kick_times:
    m = tn >= k
    duck[m] -= 0.55 * np.exp(-(tn[m] - k) * 9)
music *= np.clip(duck, 0.3, 1)

ir_len = int(2.4 * SR)
ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 6000), filt(rng.standard_normal(ir_len), "lp", 6000)]) * np.exp(-ti * 2.8)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.5

mix = music * 0.65 + sfx * 0.9 + wet
d = np.ones(N)
m = (tn > H2 - 0.1) & (tn < H2 + 0.01)
d[m] = 0.15
mix *= np.convolve(d, np.ones(240) / 240, "same")
mix += hits
mix = np.vstack([filt(mix[c], "hp", 28) for c in range(2)])

# the final Enter cuts everything
end = C["end"]
cut = np.clip((end + 0.012 - tn) / 0.012, 0, 1)
key_tail = (tn >= end) & (tn < end + 0.08)
mix = mix * cut + np.vstack([sfx[c] * key_tail * 0.9 for c in range(2)])

mix = np.tanh(mix / np.abs(mix).max() * 1.6)
mix = mix / np.abs(mix).max() * 10 ** (-1 / 20)
wavfile.write(out_path, SR, (mix.T * 32767).astype(np.int16))
print("peak", 20 * np.log10(np.abs(mix).max()), "rms", 20 * np.log10(np.sqrt((mix ** 2).mean())))
