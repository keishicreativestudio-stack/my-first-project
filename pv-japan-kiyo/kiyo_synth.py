"""Serene 60 BPM score for the 清 trailer (30 s).

Stream ambience, water drops on the ripple cues, wind chimes (furin), a few
morning birds in the bamboo scene, a shō drone and sparse koto in the bright
yo-scale (D E G A B), a soft shakuhachi line over Fuji, bells in the snow,
and a single drop + bell + koto chord on the closing seal.
Usage: python3 kiyo_synth.py ../audio/synth.py ../wa/wa_synth.py cues.json out.wav
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
YO = [62, 64, 67, 69, 71, 74, 76, 79, 81, 83, 86]   # D yo scale
tn = np.arange(N) / SR


def furin(amp=1.0, f=2600):
    d = 2.4
    t = tt(d)
    s = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * dcy) for r, a, dcy in ((1, 1, 1.4), (2.32, .5, 2.2), (4.1, .25, 3.5), (5.9, .12, 5)))
    return s * np.minimum(1, t / 0.001) * amp * 0.12


def bird(amp=1.0):
    d = 0.5
    t = tt(d)
    out = np.zeros(len(t))
    for k, st in enumerate((0, 0.12, 0.22)):
        i = int(st * SR); u = t[:len(t) - i]
        f = 3200 + 1400 * np.sin(np.pi * np.clip(u / 0.08, 0, 1)) + 300 * k
        out[i:] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.clip(u / 0.09, 0, 1))
    return out * amp * 0.08


# stream: slowly moving filtered noise under everything
st = filt(rng.standard_normal(N), "bp", (600, 4200)) * 0.035
st *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * tn) * np.sin(2 * np.pi * 0.07 * tn + 1)
gurgle = sum(filt(rng.standard_normal(N), "bp", (f * 0.9, f * 1.1)) * (0.5 + 0.5 * np.sin(2 * np.pi * r * tn)) for f, r in ((900, 3.1), (1400, 4.3), (2100, 5.7))) * 0.01
amb = (st + gurgle) * np.clip(tn / 1.5, 0, 1) * np.clip((C["end"] - 2.5 - tn) / 3, 0.25, 1)
music[0] += amb; music[1] += np.roll(amb, 311)

# shō drone that changes colour with each scene
chords = [[62, 69, 74, 76], [64, 69, 71, 76], [62, 67, 71, 74], [62, 69, 74, 79], [67, 71, 74, 76], [64, 69, 71, 76], [62, 69, 74, 81]]
sc = C["scenes"] + [27.0]
for i in range(7):
    a, b_ = sc[i], sc[i + 1]
    place(music, max(0, a - 0.8), sho(chords[i], b_ - a + 1.8, 0.5), 1.0, rev=0.6)

# koto: a few notes per scene, unhurried
phr = {0: [(1.2, 74), (2.6, 76), (3.4, 79), (4.6, 76)],
       1: [(6.2, 79), (7.0, 81), (8.2, 83, 1), (9.3, 81)],
       2: [(10.6, 86), (11.6, 83), (12.6, 81)],
       3: [(14.2, 74), (15.4, 76)],
       4: [(17.6, 79), (18.4, 76), (19.6, 74)],
       5: [(21.2, 81), (22.0, 83), (23.0, 86)],
       6: [(24.6, 74), (25.4, 79), (26.4, 76)]}
for i, notes in phr.items():
    for n in notes:
        place(music, n[0], koto(n[1], 2.6, 0.5, bend=(n[2] if len(n) > 2 else 0), bright=0.45), pan=-0.25, rev=0.6)
place(music, 13.9, shakuhachi(74, 1.8, 0.35, -1.5), pan=0.25, rev=0.7)
place(music, 15.9, shakuhachi(76, 1.3, 0.3, -1), pan=0.25, rev=0.7)

# effects on the picture cues
for td in C["drops"]:
    place(sfx, td, water_drop(0.9), rev=0.6)
    for k in range(3): place(sfx, td + 0.05 + k * 0.28, koto(YO[6 + k], 1.6, 0.18, bright=0.9), pan=0.2, rev=0.7)
for tl in C["lights"]:
    place(sfx, tl, reverse_swell(1.1, 0.25))
    place(sfx, tl + 0.9, furin(1.0, 2700), pan=0.4, rev=0.5)
for k in range(9):
    place(sfx, 0.8 + k * 3.1 + rng.uniform(0, 1), furin(0.6, rng.choice([2400, 2650, 2900])), pan=rng.uniform(-0.6, 0.6), rev=0.5)
for k in range(5):
    place(sfx, 5.8 + k * 0.85 + rng.uniform(0, .2), bird(1.0), pan=rng.uniform(-0.7, 0.7), rev=0.4)
for k in range(8):
    place(sfx, 20.8 + k * 0.4, suzu(0.3, 0.3, 10), pan=-0.5 + k * 0.14, rev=0.6)

# closing: one drop, the seal, a clear bell and the last chord
L = C["logo"]
place(sfx, L + 0.6, water_drop(1.0), rev=0.7)
place(sfx, C["seal"], bell(74, 3.0, 0.6), rev=0.7)
for k, m in enumerate([62, 69, 74, 79, 83]):
    place(music, C["seal"] + 0.1 + k * 0.07, koto(m, 2.4, 0.4, bright=0.5), pan=-0.3 + k * 0.15, rev=0.7)
place(sfx, C["seal"] + 0.9, suzu(0.8, 0.6, 30), rev=0.6)

ir_len = int(3.6 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 7000), filt(rng.standard_normal(ir_len), "lp", 7000)]) * np.exp(-ti * 1.6)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.55
out = music * 0.8 + sfx * 0.85 + wet
out = np.vstack([filt(out[c], "hp", 40) for c in range(2)])
out *= np.clip((DUR - tn) / 0.8, 0, 1) * np.clip(tn / 0.3, 0, 1)
out = np.tanh(out / np.abs(out).max() * 1.2)
out = out / np.abs(out).max() * 10 ** (-1.5 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
for a, b_ in [(0, 5.5), (5.5, 13.5), (13.5, 20.5), (20.5, 27), (27, 30)]:
    s_ = out[:, int(a * SR):int(b_ * SR)]; print(a, b_, round(20 * np.log10(np.sqrt((s_ ** 2).mean()) + 1e-9), 1))
