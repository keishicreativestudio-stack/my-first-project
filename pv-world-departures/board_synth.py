"""Airport-lounge bossa nova (120 BPM) for the DEPARTURES trailer (30 s = 15 bars).

The three-tone airport chime opens; a nylon guitar (Karplus-Strong) plays bossa thumb
bass and syncopated chords over Dm9 - G13 - Cmaj9 - A7b9, with brushes, rim clicks on the
bossa clave, an upright bass, a soft electric piano and a vibraphone melody. Every change
of the departures board rattles with split-flap clicks, and every photo mosaic flips with
a heavier wave of flaps. The Earth gets a breakdown; the logo lands on Cmaj9 with the
chime again on the call to action.
Usage: python3 board_synth.py ../audio/synth.py ../wa/wa_synth.py cues.json out.wav
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
at = lambda bar, beat=0: bar * BAR + beat * BEAT
tn = np.arange(N) / SR
r_ = np.random.default_rng(5)
_cache = {}


def nylon(m, dur):
    k = (m, round(dur, 2))
    if k in _cache: return _cache[k]
    f = midi(m); n = int(dur * SR); p = max(2, int(SR / f))
    buf = filt(np.concatenate([r_.uniform(-1, 1, p)] * 2), "lp", 2200)[:p]
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.4975 * (buf[i % p] + buf[(i + 1) % p])
    out *= np.clip((dur - np.arange(n) / SR) / 0.05, 0, 1)
    _cache[k] = out * 0.5
    return _cache[k]


def epiano(notes, dur, amp=1.0):
    t = tt(dur)
    s = np.zeros(len(t))
    for m in notes:
        f = midi(m)
        s += np.sin(2 * np.pi * f * t + 0.6 * np.sin(2 * np.pi * f * t) * np.exp(-t * 3)) * np.exp(-t * 1.2)
        s += 0.15 * np.sin(2 * np.pi * f * 7 * t) * np.exp(-t * 14)
    trem = 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)
    return s * trem * np.minimum(1, t / 0.004) * np.clip((dur - t) / 0.2, 0, 1) * amp * 0.12 / max(1, len(notes) ** 0.5)


def vibes(m, dur, amp=1.0):
    t = tt(dur + 0.6)
    f = midi(m)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 6)
    return s * np.exp(-t * 1.6) * (1 + 0.25 * np.sin(2 * np.pi * 5.5 * t)) * np.minimum(1, t / 0.002) * amp * 0.25


def ubass(m, dur, amp=1.0):
    t = tt(dur)
    f = midi(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) * np.exp(-t * 6)
    return s * np.minimum(1, t / 0.006) * np.exp(-t * 2) * np.clip((dur - t) / 0.03, 0, 1) * amp * 0.5


def brush(dur, amp=1.0):
    t = tt(dur)
    sw = filt(noise(dur), "bp", (1800, 7000)) * (0.3 + 0.7 * np.sin(np.pi * np.clip(t / dur, 0, 1)))
    return sw * amp * 0.06


def tap(amp=1.0):
    d = 0.15
    t = tt(d)
    return filt(noise(d), "bp", (1500, 6000)) * np.exp(-t * 35) * amp * 0.25


def rim(amp=1.0):
    d = 0.08
    t = tt(d)
    return (np.sin(2 * np.pi * 1750 * t) * np.exp(-t * 110) * 0.7 + filt(noise(d), "bp", (2500, 7000)) * np.exp(-t * 140)) * amp * 0.3


def flap(amp=1.0, heavy=False):
    d = 0.05
    t = tt(d)
    f0 = r_.uniform(2200, 4200) * (0.6 if heavy else 1)
    s = filt(noise(d), "bp", (f0 * 0.6, f0 * 1.6)) * np.exp(-t * (180 if not heavy else 120))
    s += np.sin(2 * np.pi * (380 if heavy else 700) * t) * np.exp(-t * 200) * 0.4
    return s * amp * (0.5 if heavy else 0.32)


def chime3(amp=1.0):
    out = np.zeros(int(3.0 * SR))
    for k, (m, st) in enumerate(((76, 0.0), (79, 0.32), (84, 0.64))):
        t = tt(2.2); f = midi(m)
        s = (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 3)) * np.exp(-t * 1.8) * np.minimum(1, t / 0.005)
        i = int(st * SR); out[i:i + len(s)] += s[:len(out) - i]
    return out * amp * 0.25


CH = {"Dm9": (38, [53, 57, 60, 64]), "G13": (43, [53, 59, 64]), "Cmaj9": (36, [52, 55, 59, 62]), "A7b9": (45, [55, 61, 64, 70])}
PROG = ["Dm9", "G13", "Cmaj9", "A7b9"]
MEL = {"Dm9": [(0, 69, 2), (2, 72, 1), (3, 76, 1), (4, 74, 2), (6, 72, 2)],
       "G13": [(0, 71, 1), (1, 72, 1), (2, 74, 2), (4, 76, 3), (7, 74, 1)],
       "Cmaj9": [(0, 76, 3), (3, 74, 1), (4, 71, 2), (6, 67, 2)],
       "A7b9": [(0, 69, 1), (1, 70, 1), (2, 73, 2), (4, 76, 2), (6, 79, 2)]}
COMP = [[0, 3, 6], [2, 5]]           # syncopated chord hits in 8ths, two-bar bossa pattern
CLAVE = [[0, 3, 6], [2, 4]]


def bar(b, drums=True, mel=1.0, ep=1.0, oct_=False):
    name = PROG[b % 4]; root, notes = CH[name]; t0 = at(b)
    for q, m in ((0, root), (2, root + 7)):
        place(music, t0 + q * BEAT, nylon(m, BEAT * 1.8) * 0.9, pan=-0.2, rev=0.15)
        place(music, t0 + q * BEAT, ubass(m, BEAT * 1.8, 0.8), 1.0)
    for e in COMP[b % 2]:
        for k, m in enumerate(notes): place(music, t0 + e * E8 + k * 0.004, nylon(m + 12 if m < 55 else m, E8 * 1.6) * 0.55, pan=-0.25, rev=0.2)
    if ep: place(music, t0, epiano(notes, BAR * 0.95, ep), pan=0.2, rev=0.35)
    if drums:
        for q in range(4):
            place(music, t0 + q * BEAT, brush(BEAT, 1.0), pan=0.25)
            place(music, t0 + q * BEAT + E8, tap(0.5), pan=0.2)
        for e in CLAVE[b % 2]: place(music, t0 + e * E8, rim(0.9), pan=0.3, rev=0.15)
    if mel:
        for e, m, ln in MEL[name]:
            place(music, t0 + e * E8, vibes(m, E8 * ln, mel), pan=0.1, rev=0.35)
            if oct_: place(music, t0 + e * E8, vibes(m + 12, E8 * ln, mel * 0.4), pan=-0.1, rev=0.35)


# ---------------- intro (bar 0): chime and guitar alone
place(sfx, 0.08, chime3(1.0), pan=0.1, rev=0.5)
root, notes = CH["Dm9"]
for e in (0, 3, 6):
    for k, m in enumerate(notes): place(music, at(0) + e * E8 + k * 0.004, nylon(m + 12 if m < 55 else m, E8 * 1.6) * 0.5, pan=-0.25, rev=0.3)
place(music, at(0, 2.5), vibes(81, E8 * 2, 0.7), rev=0.4); place(music, at(0, 3.5), vibes(79, E8, 0.6), rev=0.4)
# ---------------- groove (bars 1-11)
for b in range(1, 12): bar(b, mel=0.9 if b < 9 else 1.0, oct_=b >= 10)
# the fast cities: a rim on every cut
for f in C["fast"]: place(sfx, f, rim(1.2), pan=-0.2, rev=0.2)
# ---------------- earth breakdown (bars 12-13, until the logo)
for b in (12, 13):
    name = PROG[b % 4]; root, notes = CH[name]
    place(music, at(b), epiano(notes, BAR * 0.95, 1.3), pan=0.2, rev=0.5)
    place(music, at(b), ubass(root, BAR * 0.9, 0.8), 1.0)
    for e, m, ln in MEL[name][:3]: place(music, at(b) + e * E8, vibes(m, E8 * ln, 0.8), rev=0.5)
place(sfx, C["earth"], chime3(0.5), pan=-0.1, rev=0.6)
# ---------------- logo: Cmaj9 rings out
L = C["logo"]
root, notes = CH["Cmaj9"]
place(music, L, ubass(36, 2.8, 1.0), 1.0)
for k, m in enumerate([48, 52, 55, 59, 62, 67]): place(music, L + k * 0.03, nylon(m, 3.0) * 0.7, pan=-0.25 + k * 0.08, rev=0.4)
place(music, L, epiano(notes + [67], DUR - L, 1.2), pan=0.2, rev=0.5)
for k, m in enumerate([76, 79, 83, 86]): place(music, L + 0.2 + k * 0.12, vibes(m, 1.2, 0.7), pan=-0.2 + k * 0.13, rev=0.5)
place(sfx, C["cta"], chime3(0.8), pan=0.1, rev=0.6)

# ---------------- split-flap clicks
for bt in C["board"]:
    n = 60
    for k in range(n):
        tk = bt + (k / n) ** 0.8 * 0.55 + r_.uniform(0, 0.02)
        place(sfx, tk, flap(r_.uniform(0.5, 1.0)), pan=r_.uniform(-0.6, -0.1))
for mt in C["mosaic"]:
    for k in range(48):
        tk = mt + (k % 14) * 0.026 + r_.uniform(0, 0.12)
        place(sfx, tk, flap(r_.uniform(0.6, 1.0), heavy=True), pan=r_.uniform(-0.5, 0.5))
for k in range(30): place(sfx, L + 0.1 + r_.uniform(0, 1.0), flap(r_.uniform(0.6, 1.0), heavy=bool(k % 2)), pan=r_.uniform(-0.4, 0.4))

# ---------------- mix
ir_len = int(1.6 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 6000), filt(rng.standard_normal(ir_len), "lp", 6000)]) * np.exp(-ti * 3.2)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.35
out = music * 0.85 + sfx * 0.7 + wet
out = np.vstack([filt(out[c], "hp", 35) for c in range(2)])
out *= np.clip(tn / 0.05, 0, 1) * np.clip((DUR - tn) / 0.6, 0, 1)
out = np.tanh(out / np.abs(out).max() * 1.8)
out = out / np.abs(out).max() * 10 ** (-0.8 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
for a, b_ in [(0, at(1)), (at(1), at(9)), (at(9), at(12)), (at(12), L), (L, DUR)]:
    s_ = out[:, int(a * SR):int(b_ * SR)]
    print(round(a, 2), round(b_, 2), round(20 * np.log10(np.sqrt((s_ ** 2).mean()) + 1e-9), 1))
