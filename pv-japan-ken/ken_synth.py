"""Dark 96 BPM trap x taiko score for the 一閃 trailer (30 s).

Intro: low drone, shakuhachi breath, a lone odaiko. Build (from the first cut):
half-time kick, ticking hats. Kanji run (8.75-18.75 s): full trap groove with 808
glides, rolling hats, koto ostinato in the dark in-scale. Every cut gets a sword
"shing" (whoosh + metallic ring). Strikes: odaiko + boom hits over a riser,
a breath of silence, then the AI hit. Logo: last slash, hit and ring-out.
Usage: python3 ken_synth.py ../audio/synth.py ../wa/wa_synth.py cues.json out.wav
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
BEAT = 60 / C["bpm"]; BAR = BEAT * 4
B = lambda b: b * BEAT
tn = np.arange(N) / SR
IN = [50, 51, 55, 57, 58, 62, 63, 67, 69, 70, 74]   # D in-scale
kicks = []


def shing(amp=1.0, seed=0):
    d = 1.6
    t = tt(d)
    r = np.random.default_rng(seed)
    wh = sweep_filter(noise(d), "bp", 600, 9000) * np.exp(-((t - 0.06) / 0.05) ** 2) * 1.2
    f0 = 2300 + 400 * r.random()
    ring = sum(a * np.sin(2 * np.pi * f0 * k * (1 + 0.004 * np.exp(-t * 6)) * t) * np.exp(-t * dc)
               for k, a, dc in ((1, 1, 2.2), (1.51, .6, 3), (2.37, .45, 4), (3.9, .3, 6), (5.3, .2, 8)))
    ring *= np.clip((t - 0.05) / 0.004, 0, 1) * 0.35
    return (wh + ring) * amp


def k808(m, dur, amp=1.0, glide_from=None):
    t = tt(dur)
    f = midi(m) * np.ones(len(t))
    if glide_from is not None: f = midi(m) + (midi(glide_from) - midi(m)) * np.exp(-t * 18)
    f = f + 90 * np.exp(-t * 40)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return np.tanh(s * 1.8) * np.minimum(1, t / 0.003) * np.clip((dur - t) / 0.05, 0, 1) * np.exp(-t * 0.8) * amp * 0.8


def clap(amp=1.0):
    d = 0.3
    t = tt(d)
    env = np.zeros(len(t))
    for off in (0, 0.012, 0.024):
        i = int(off * SR); env[i:] += np.exp(-t[:len(t) - i] * 35)
    return filt(noise(d), "bp", (900, 6000)) * env * amp * 0.45


def drone(dur, amp=1.0):
    t = tt(dur)
    s = sum(np.sin(2 * np.pi * midi(m) * t + 0.3 * np.sin(2 * np.pi * 0.2 * t * (i + 1))) * a
            for i, (m, a) in enumerate(((26, 1), (38, .6), (45, .3), (50, .15))))
    s += filt(noise(dur), "lp", 300) * 0.4
    return s * np.minimum(1, t / 1.5) * np.clip((dur - t) / 0.5, 0, 1) * amp * 0.35


# ---------------- intro 0 - B(6)
place(music, 0, drone(B(22), 1.0), pan=0, rev=0.3)
place(sfx, 0.0, odaiko(1.1), rev=0.5); place(sfx, 0.0, boom(2.0), 0.7)
place(music, 0.4, shakuhachi(62, 1.6, 0.6, bend_from=-2), pan=-0.2, rev=0.6)
place(music, 2.1, shakuhachi(63, 1.0, 0.5), pan=-0.2, rev=0.6)
place(music, B(4), shakuhachi(58, 1.2, 0.45, bend_from=-1), pan=-0.2, rev=0.6)
for b in range(0, 6): place(music, B(b) + B(0.5), hat(0.15), pan=0.3)

# ---------------- build B(6) - B(14): half-time kick, ticking hats, 808 enters
for b in range(6, 14):
    tb = B(b)
    if b % 4 in (0,): place(music, tb, k808(38, B(2), 0.9), 1.0); kicks.append(tb)
    if b % 4 == 2: place(music, tb, clap(0.8), rev=0.25)
    for s in range(2): place(music, tb + s * B(0.5), hat(0.3 if s else 0.2), pan=0.25)
    if b % 2 == 0: place(music, tb, koto(IN[b % 5 + 2], 1.0, 0.35, bright=0.4), pan=0.3, rev=0.4)
place(sfx, B(10), riser(B(4), 200, 5000, 0.6), rev=0.3)
place(sfx, B(14) - B(0.75), reverse_swell(B(0.75), 0.8))

# ---------------- kanji run B(14) - B(30): full trap groove
OST = [62, 63, 67, 69, 70, 69, 67, 63]
BASS = [38, 38, 34, 36]
for b in range(14, 30):
    tb = B(b); bar = (b - 14) // 4; pos = (b - 14) % 4
    root = BASS[bar % 4]
    if pos == 0:
        place(music, tb, k808(root, B(1.5), 1.0, glide_from=root + 12 if bar else None), 1.0); kicks.append(tb)
    if pos == 1: place(music, tb + B(0.75), k808(root, B(0.25), 0.8), 1.0); kicks.append(tb + B(0.75))
    if pos == 2: place(music, tb, clap(1.0), rev=0.2); place(music, tb, snare(0.5), rev=0.2)
    if pos == 3 and bar % 2 == 1: place(music, tb + B(0.5), k808(root + 3, B(0.5), 0.8), 1.0)
    roll = 6 if pos == 3 and bar % 2 == 0 else 4
    for s in range(roll): place(music, tb + s * BEAT / roll, hat(0.28 + 0.1 * (s % 2 == 0)), pan=0.3 - 0.2 * (s % 2))
    for e in range(2):
        m = OST[(pos * 2 + e) % 8] + (12 if bar >= 2 else 0)
        place(music, tb + e * B(0.5), koto(m, 0.7, 0.32, bright=0.6), pan=-0.3, rev=0.35)
place(music, B(14), sho([62, 69, 74], B(16), 0.35), rev=0.4)
for h in (B(14), B(22)):
    place(sfx, h, odaiko(1.2), rev=0.4); place(sfx, h, crash(2.0, 0.6), rev=0.4)
place(sfx, B(26), riser(B(4), 300, 9000, 0.7), rev=0.3)

# ---------------- strikes B(30) - B(36)
for i, st in enumerate(C["strikes"]):
    place(sfx, st, odaiko(1.3 + 0.1 * i), rev=0.45); place(sfx, st, boom(1.6), 0.4 + 0.08 * i)
    place(sfx, st, shime(0.8), pan=0.2)
place(music, B(30), drone(B(6), 1.2), rev=0.3)
for b in range(30, 35):
    for s in range(4): place(music, B(b) + s * B(0.25), hat(0.2 + 0.05 * (b - 30)), pan=0.3)
place(sfx, B(32), riser(B(3.6), 200, 12000, 1.0), rev=0.3)
place(sfx, C["ai"] - B(0.9), reverse_swell(B(0.9), 1.0))

# ---------------- AI hit + tail to logo
ai = C["ai"]
place(sfx, ai, odaiko(1.8), rev=0.6); place(sfx, ai, boom(3.0), 1.3); place(sfx, ai, crash(3.0, 1.1), rev=0.5)
place(sfx, ai, k808(26, 2.4, 1.2, glide_from=38), 1.0)
place(music, ai, sho([50, 57, 62, 69], B(4), 0.5), rev=0.5)
for b in range(36, 40):
    if b % 2 == 0: place(music, B(b), k808(38, B(1), 0.7), 1.0); kicks.append(B(b))
    place(music, B(b) + B(0.5), hat(0.2), pan=0.3)
place(music, B(38), shakuhachi(62, 1.4, 0.5, bend_from=-2), pan=-0.2, rev=0.6)

# ---------------- logo
lg = C["logo"]
place(sfx, lg, odaiko(1.6), rev=0.7); place(sfx, lg, boom(3.0), 1.1); place(sfx, lg, crash(3.5, 0.7), rev=0.6)
for k, m in enumerate([50, 57, 62, 63, 69]):
    place(music, lg + k * 0.06, koto(m, 3.0, 0.5, bright=0.6), pan=-0.3 + k * 0.15, rev=0.6)
place(music, lg, drone(DUR - lg, 0.8), rev=0.4)
place(sfx, C["cta"], bell(86, 2.5, 0.5), pan=0.2, rev=0.6)
place(sfx, C["cta"], hyoshigi(0.6), pan=-0.1, rev=0.4)

# ---------------- sword cuts
for i, c in enumerate(C["slashes"]):
    big = c in (C["ai"], lg, B(6), B(14))
    place(sfx, c - 0.04, shing(1.3 if big else 0.95, seed=i), pan=(-0.25 if i % 2 else 0.25), rev=0.35)

# ---------------- mix
duck = np.ones(N)
for k in kicks:
    m = (tn >= k) & (tn < k + BEAT)
    duck[m] = np.minimum(duck[m], 0.5 + 0.5 * np.clip((tn[m] - k) / (BEAT * 0.6), 0, 1))
music *= duck
lift = np.interp(tn, [0, B(6), B(14) - 0.05, B(14), B(30), B(30) + 0.3], [0.8, 0.9, 1.0, 1.5, 1.5, 1.0])
music *= lift
ir_len = int(2.4 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 6000), filt(rng.standard_normal(ir_len), "lp", 6000)]) * np.exp(-ti * 2.4)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.4
out = music * 0.8 + sfx * 0.9 + wet
gate = np.ones(N)
gate[(tn > ai - B(0.9) + 0.02) & (tn < ai - 0.02)] = 0.25
gate = np.convolve(gate, np.ones(240) / 240, "same")
out = np.vstack([filt(out[c], "hp", 25) * gate for c in range(2)])
out *= np.clip((DUR - tn) / 0.6, 0, 1)
out = np.tanh(out / np.abs(out).max() * 1.8)
out = out / np.abs(out).max() * 10 ** (-0.8 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
for a, b_ in [(0, B(6)), (B(6), B(14)), (B(14), B(30)), (B(30), ai), (ai, lg), (lg, DUR)]:
    s_ = out[:, int(a * SR):int(b_ * SR)]
    print(round(a, 2), round(b_, 2), round(20 * np.log10(np.sqrt((s_ ** 2).mean()) + 1e-9), 1))
