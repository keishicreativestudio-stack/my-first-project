"""96 BPM cinematic score for the AIチャレンジ365 trailer (30 s, 12 bars).

Act 1 (bars 0-3): shō drone, koto phrases in miyako-bushi, shakuhachi, a
water drop, soft distant taiko. Act 2 (bars 4-7): taiko groove that thickens,
koto ostinato, a whoosh on every cut, riser and shime roll, a breath of
silence. Climax (bars 8-9): huge hits with sub boom, crash and a low brass-like
swell, heavy taiko. Resolve (bars 10-11): shō and bells through the torii,
reverse swell, a final hit on the logo, a seal thud, koto ring-out.
Reuses the instrument code of synth.py and wa_synth.py.
Usage: python3 japan_synth.py ../audio/synth.py ../wa/wa_synth.py cues.json out.wav
"""
import sys
import numpy as np

base, wa_path, cues_path, out_path = sys.argv[1:5]
src = open(base).read()
src = src[:src.index("# ---------------------------------------------------------------- arrangement")].replace("DUR = 13.5", "DUR = 30.0")
sys.argv = [base, cues_path, out_path]
exec(src)                                   # buses, place(), filters, boom, crash, riser, reverse_swell, pad ...
wa = open(wa_path).read()
exec(wa[wa.index("\n# ---------------------------------------------------------------- instruments"):wa.index("\n# ---------------------------------------------------------------- arrangement")])

C = cues
BEAT = 60 / C["bpm"]; BAR = BEAT * 4
MIYAKO = [52, 53, 57, 59, 60, 64, 65, 69, 71, 72, 76, 77, 81, 83, 84]


def braam(dur=2.4, amp=1.0):
    t = tt(dur)
    s = sum(saw(midi(m), dur, detune=d, maxf=2400) for m, d in ((28, 0), (40, -8), (40, 8), (47, 0)))
    s = sweep_filter(s, "lp", 200, 1200)
    return np.tanh(s * 1.6) * np.minimum(1, t / 0.04) * np.exp(-t * 1.2) * amp * 0.6


def whoosh(dur=0.3, amp=1.0):
    t = tt(dur)
    return sweep_filter(noise(dur), "bp", 500, 6000) * np.sin(np.pi * t / dur) ** 2 * amp * 0.45


# ---------------- act 1
place(music, 0.0, sho([57, 64, 69, 71], BAR * 4 + 0.5, 1.1), 1.0, rev=0.5)
place(sfx, 0.05, water_drop(0.8), rev=0.5)
phr = [(0.3, 64), (0.9, 69), (1.5, 71, 1), (2.9, 72), (3.5, 71), (4.1, 69), (5.4, 76), (6.0, 77, 1), (6.6, 76), (7.9, 72), (8.5, 71), (9.1, 69)]
for p in phr:
    place(music, p[0], koto(p[1], 2.4, 0.85, bend=(p[2] if len(p) > 2 else 0)), pan=-0.2, rev=0.5)
for tb in (BAR * 2, BAR * 3):
    place(music, tb, odaiko(0.45), 1.0, rev=0.4)
place(music, BAR * 2 + 0.3, shakuhachi(69, 1.6, 0.5, -1.5), pan=0.2, rev=0.6)
place(music, BAR * 3 + 0.2, shakuhachi(72, 1.2, 0.45, -1), pan=0.2, rev=0.6)
for ct in C["cuts"][1:4]:
    place(sfx, ct - 0.7, brush_swish(0.8, 0.7), pan=0.1, rev=0.3)       # ink bleed
place(sfx, BAR * 4 - 0.9, reverse_swell(0.9, 0.8))

# ---------------- act 2
riff = [64, 69, 71, 72, 71, 69, 64, 71]
for bar in range(4, 8):
    t0 = bar * BAR
    for beat in range(4):
        tb = t0 + beat * BEAT
        if beat in (0, 2) or (bar >= 6 and beat == 3):
            place(music, tb, odaiko(0.8 if beat == 0 else 0.6), 1.0, rev=0.25)
        for s16 in range(4):
            if bar >= 5 or s16 % 2 == 0:
                place(music, tb + s16 * BEAT / 4, shime(0.25 + 0.2 * (s16 == 0) + 0.05 * (bar - 4)), pan=0.3)
        place(music, tb + BEAT / 2, ka(0.5), pan=-0.35)
    for e in range(8):
        place(music, t0 + e * BEAT / 2, koto(riff[e] + (12 if bar >= 6 and e % 2 else 0), 1.0, 0.35, bright=0.6), pan=-0.3, rev=0.25)
    place(music, t0, sho([57, 64, 69, 72] if bar % 2 == 0 else [55, 62, 67, 71], BAR, 0.4), 1.0, rev=0.3)
for w in C["whips"]:
    place(sfx, w - 0.12, whoosh(0.3, 0.8), pan=0.2)
place(sfx, BAR * 7, riser(BAR - 0.15, 250, 9000, 0.8), rev=0.3)
place(sfx, BAR * 7.5, reverse_swell(BAR / 2 - 0.12, 1.0))
t = BAR * 7.5
while t < BAR * 8 - 0.14:
    place(music, t, shime(0.2 + 0.7 * (t - BAR * 7.5) / (BAR / 2)), pan=0.1)
    t += max(0.035, 0.12 * (1 - (t - BAR * 7.5) / (BAR / 2 + 0.2)))

# ---------------- climax
hits = [BAR * 8, BAR * 9]
for h in hits:
    place(sfx, h, odaiko(1.5), 1.0, rev=0.5)
    place(sfx, h, boom(2.6), 1.0)
    place(sfx, h, crash(2.4, 0.9), rev=0.5)
    place(sfx, h, braam(2.4, 1.0), rev=0.4)
for ts in C["taikoStrikes"][1:]:
    place(sfx, ts, odaiko(1.0), 1.0, rev=0.3)
for bar in (8, 9):
    t0 = bar * BAR
    for beat in range(4):
        for s16 in range(4):
            place(music, t0 + beat * BEAT + s16 * BEAT / 4, shime(0.35 + 0.25 * (s16 == 0)), pan=0.3)
    for e, m in enumerate([76, 77, 81, 83, 81, 77, 76, 72] if bar == 8 else [72, 76, 77, 81, 84, 81, 77, 76]):
        place(music, t0 + e * BEAT / 2, koto(m, 1.2, 0.5, bright=0.7), pan=-0.3, rev=0.3)
    place(music, t0, sho([52, 59, 64, 69, 71], BAR, 0.6), 1.0, rev=0.4)
place(sfx, BAR * 9 + 0.05, whoosh(1.2, 1.0), pan=-0.3)                   # wind over the grass

# ---------------- resolve
r0 = BAR * 10
place(music, r0, sho([69, 71, 76, 81, 83], BAR + 0.4, 0.8), 1.0, rev=0.6)
for k in range(8):
    place(sfx, r0 + 0.2 + k * 0.28, suzu(0.3, 0.4, 12), pan=-0.5 + k * 0.13, rev=0.5)
for k, m in enumerate(MIYAKO[4:13]):
    place(music, r0 + 0.1 + k * 0.05, koto(m, 2.0, 0.3, bright=0.8), pan=-0.4 + k * 0.1, rev=0.5)
place(sfx, BAR * 11 - 1.1, reverse_swell(1.1, 1.0))
L = C["logo"]
place(sfx, L, odaiko(1.4), 1.0, rev=0.6)
place(sfx, L, boom(2.2), 0.8)
for k, m in enumerate([64, 69, 71, 76, 81]):
    place(music, L + k * 0.06, koto(m, 2.4, 0.5), pan=-0.3 + k * 0.15, rev=0.6)
place(sfx, C["stamp"], stamp(0.9))
place(sfx, C["stamp"], hyoshigi(0.6), rev=0.3)
place(sfx, C["cta"], suzu(0.8, 0.7, 40), pan=0.2, rev=0.5)

# ---------------- mix
tn = np.arange(N) / SR
ir_len = int(3.2 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 5000), filt(rng.standard_normal(ir_len), "lp", 5000)]) * np.exp(-ti * 1.8)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.5
out = music * 0.75 + sfx * 0.9 + wet
# the breath before the climax: everything drops out for the last 0.12 s of bar 7
gate = np.ones(N); gate[(tn > BAR * 8 - 0.12) & (tn < BAR * 8)] = 0
gate = np.convolve(gate, np.ones(200) / 200, "same"); out *= gate
out = np.vstack([filt(out[c], "hp", 30) for c in range(2)])
out *= np.clip((DUR - tn) / 0.6, 0, 1)
out = np.tanh(out / np.abs(out).max() * 1.4)
out = out / np.abs(out).max() * 10 ** (-1 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
for a, b_ in [(0, 10), (10, 20), (20, 25), (25, 27.5), (27.5, 30)]:
    s_ = out[:, int(a * SR):int(b_ * SR)]; print(a, b_, round(20 * np.log10(np.sqrt((s_ ** 2).mean()) + 1e-9), 1))
