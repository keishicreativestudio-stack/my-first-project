"""Bright 128 BPM J-pop / future-funk score for the POP trailer (30 s = 16 bars).

Royal-road progression in C (F G Em Am) with four-on-the-floor kick, claps, off-beat
hats, a bouncing octave bass, off-beat pluck chords and a square-wave + glockenspiel hook.
Every sticker gets a bubble pop, every word a sparkle, every colour wipe a whoosh.
The grid pops in rising sixteenths, the day counter climbs with a ticking arpeggio and
lands on a ding. Bars 12-13 build with a snare roll to half a beat of silence; the logo
drops with a crash, full groove, a chime cascade and a ding on the call to action.
Usage: python3 pop_synth.py ../audio/synth.py ../wa/wa_synth.py cues.json out.wav
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
B = lambda b: b * BEAT
tn = np.arange(N) / SR
kicks = []


def square(m, dur, amp=1.0, duty=0.5, cutoff=6000):
    t = tt(dur)
    ph = (midi(m) * t) % 1
    s = np.where(ph < duty, 1.0, -1.0) + 0.4 * np.sin(2 * np.pi * midi(m) * t)
    s = filt(s, "lp", cutoff)
    return s * np.minimum(1, t / 0.004) * np.exp(-t * 3) * np.clip((dur - t) / 0.02, 0, 1) * amp * 0.25


def pbass(m, dur, amp=1.0):
    t = tt(dur)
    f = midi(m)
    s = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.3 for k in range(1, 7))
    cut = np.exp(-t * 18)
    s = s * (0.55 + 0.45 * cut)
    return s * np.minimum(1, t / 0.003) * np.clip((dur - t) / 0.02, 0, 1) * amp * 0.45


def bubble(amp=1.0, f0=380, f1=1500):
    d = 0.09
    t = tt(d)
    f = f0 + (f1 - f0) * (t / d) ** 0.6
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.7 * np.exp(-t * 18) * amp * 0.7


def sparkle(amp=1.0, seed=0):
    r = np.random.default_rng(seed)
    out = np.zeros(int(0.5 * SR))
    for k in range(5):
        b = bell(96 + r.integers(0, 8), 0.4, 0.25)
        i = int(k * 0.035 * SR); out[i:i + len(b)] += b[:len(out) - i]
    return out * amp


def whoosh(dur=0.3, amp=1.0):
    t = tt(dur)
    return sweep_filter(noise(dur), "bp", 800, 6000) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2 * amp * 0.5


def clap(amp=1.0):
    d = 0.25
    t = tt(d)
    env = np.zeros(len(t))
    for off in (0, 0.01, 0.02):
        i = int(off * SR); env[i:] += np.exp(-t[:len(t) - i] * 40)
    return filt(noise(d), "bp", (1000, 6000)) * env * amp * 0.45


CH = {"F": (41, [65, 69, 72, 76]), "G": (43, [67, 71, 74, 77]), "Em": (40, [64, 67, 71, 74]), "Am": (45, [64, 69, 72, 76])}
PROG = ["F", "G", "Em", "Am"]
HOOK = {"F": [(0, 77), (1, 76), (2, 77), (3, 81), (4, 79), (6, 77), (7, 76)],
        "G": [(0, 74), (1, 76), (2, 79), (4, 79), (5, 81), (6, 79), (7, 76)],
        "Em": [(0, 76), (1, 74), (2, 76), (3, 79), (4, 83), (6, 81), (7, 79)],
        "Am": [(0, 81), (2, 79), (3, 76), (4, 72), (6, 74), (7, 76)]}


def bar(b, drums=True, bass=True, chords=True, hook=0.0, glock=0.0, hats=True):
    t0 = b * BAR; name = PROG[b % 4]; root, notes = CH[name]
    for q in range(4):
        tb = t0 + q * BEAT
        if drums:
            place(music, tb, kick(0.95, 0.4, 48, 160), 1.0); kicks.append(tb)
            if q % 2: place(music, tb, clap(1.0), pan=0.05, rev=0.2)
        if hats:
            place(music, tb + E8, hat(0.5, open_=True), pan=0.3)
            place(music, tb + E8 * 0.5, hat(0.2), pan=-0.3); place(music, tb + E8 * 1.5, hat(0.2), pan=-0.3)
    for e in range(8):
        te = t0 + e * E8
        if bass: place(music, te, pbass(root + (12 if e % 2 else 0), E8 * 0.85, 1.0), 1.0)
        if chords and e % 2 == 1:
            for k, m in enumerate(notes): place(music, te, pluck(m, E8 * 0.9, 1.2) * 0.35, pan=-0.4 + k * 0.27, rev=0.2)
    for e, m in HOOK[name]:
        if hook: place(music, t0 + e * E8, square(m, E8 * 1.3, hook, 0.25), pan=0.15, rev=0.25)
        if glock: place(music, t0 + e * E8, bell(m + 12, 0.8, glock), pan=-0.2, rev=0.3)


# ---------------- arrangement (16 bars)
bar(0, hook=0.0, glock=0.6); bar(1, glock=0.6)
bar(2, hook=0.8); bar(3, hook=0.8)
for b in range(4, 10): bar(b, hook=0.9, glock=0.35 if b >= 6 else 0.0)
bar(10, hook=0.0, glock=0.0); bar(11, hook=0.0, glock=0.0, chords=False)
bar(12, drums=False, hook=0.8); bar(13, drums=False, hats=False, hook=0.0)
bar(14, hook=1.0, glock=0.5); bar(15, hook=1.0, glock=0.5)
place(sfx, 0.0, crash(1.8, 0.6), rev=0.3)

# grid: sixteenth pops rising, counter ticks climbing, ding on landing
for i, tp in enumerate([p for p in C["pops"] if p >= C["grid"] - 1e-6]):
    place(sfx, tp, bubble(0.9, 350 + i * 40, 1200 + i * 90), pan=(i % 3 - 1) * 0.35)
c0, c1 = C["counter"]
tk = c0; k = 0
while tk < c1:
    place(sfx, tk, bell(84 + (k % 12), 0.15, 0.4), pan=0.2 if k % 2 else -0.2)
    tk += BEAT / 4; k += 1
place(sfx, c1, bell(96, 1.4, 0.9), rev=0.4); place(sfx, c1, bell(91, 1.4, 0.6), rev=0.4)
place(sfx, c0, whoosh(0.35, 1.0))

# build (bars 12-13): snare roll into half a beat of silence
tr = C["build"]; drop = C["drop"]
while tr < drop - BEAT / 2 - 1e-6:
    k = (tr - C["build"]) / (drop - C["build"])
    place(music, tr, snare(0.25 + 0.6 * k), rev=0.15)
    tr += BEAT / (2 if k < 0.5 else 4)
place(music, B(48), kick(0.9), 1.0); place(music, B(50), kick(0.9), 1.0)
place(sfx, C["build"], riser(drop - C["build"] - BEAT / 2, 300, 10000, 0.8), rev=0.3)

# drop + logo
place(sfx, drop, crash(2.5, 1.0), rev=0.4); place(sfx, drop, boom(1.6), 0.6)
for k in range(10): place(sfx, drop + k * BEAT / 4, bell(84 + [0, 4, 7, 12, 16, 19, 24, 19, 16, 12][k], 0.6, 0.45), pan=-0.4 + k * 0.08, rev=0.3)
place(sfx, C["cta"], bell(96, 1.5, 0.7), rev=0.4); place(sfx, C["cta"], bubble(1.0, 500, 1800))

# sfx: bubble pops for stickers / words, sparkles on words, whooshes on wipes
for i, tp in enumerate(C["pops"]):
    if tp >= C["grid"] - 1e-6: continue
    place(sfx, tp, bubble(1.0, 330 + (i % 5) * 60, 1300 + (i % 5) * 150), pan=(-0.3 if i % 2 else 0.3))
for i, tw in enumerate(C["words"]):
    place(sfx, tw, sparkle(0.7, seed=i), pan=0.2, rev=0.3)
for tw in C["wipes"]:
    place(sfx, tw - 0.12, whoosh(0.3, 0.7), pan=0.0)

# ---------------- mix
duck = np.ones(N)
for k in kicks:
    m = (tn >= k) & (tn < k + BEAT)
    duck[m] = np.minimum(duck[m], 0.45 + 0.55 * np.clip((tn[m] - k) / (BEAT * 0.5), 0, 1))
music *= duck
ir_len = int(1.4 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 8000), filt(rng.standard_normal(ir_len), "lp", 8000)]) * np.exp(-ti * 4)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.35
out = music * 0.8 + sfx * 0.75 + wet
gate = np.ones(N)
gate[(tn > drop - BEAT / 2 + 0.01) & (tn < drop - 0.01)] = 0.1
gate = np.convolve(gate, np.ones(240) / 240, "same")
out = np.vstack([filt(out[c], "hp", 30) * gate for c in range(2)])
out *= np.clip((DUR - tn) / 0.3, 0, 1)
out = np.tanh(out / np.abs(out).max() * 1.7)
out = out / np.abs(out).max() * 10 ** (-0.8 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
for a, b_ in [(0, B(8)), (B(8), B(16)), (B(16), B(40)), (B(40), B(48)), (B(48), drop), (drop, DUR)]:
    s_ = out[:, int(a * SR):int(b_ * SR)]
    print(round(a, 2), round(b_, 2), round(20 * np.log10(np.sqrt((s_ ** 2).mean()) + 1e-9), 1))
