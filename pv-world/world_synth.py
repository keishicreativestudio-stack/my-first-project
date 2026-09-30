"""Bright 120 BPM tropical-house score for the 世界一周 trailer (30 s = 15 bars).

Intro (bars 0-1): the cabin chime, engine hum, filtered marimba chords opening up, a
riser and a jet pass as the camera dives through the window. Groove (bars 2-7):
four-on-the-floor kick, claps, off-beat hats, shakers, octave bass, marimba chords and
a marimba hook over F#m D A E; a whoosh on every cut, a stamp thump on every stamp.
Bar 8: three stabs on the last three cities, then a beat of silence ("LAST STOP").
Drop (bars 9-10, the aurora): full groove, supersaw chords, lead in octaves, vocal chops.
Earth (bars 11-12): breakdown, pads and arpeggio, riser. Logo (bars 13-14): the groove
returns, a ding on the call to action, a final chord.
Usage: python3 world_synth.py ../audio/synth.py ../wa/wa_synth.py cues.json out.wav
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


def marimba(m, dur=0.6, amp=1.0):
    t = tt(dur)
    f = midi(m)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 6) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 22) + 0.12 * np.sin(2 * np.pi * f * 9.8 * t) * np.exp(-t * 60)
    return s * np.minimum(1, t / 0.002) * amp * 0.6


def supersaw(notes, dur, cutoff=5000, amp=1.0):
    n = int(dur * SR)
    out = np.zeros((2, n))
    for m in notes:
        for det, ch in ((-12, 0), (-4, 1), (0, 0), (0, 1), (5, 0), (13, 1)):
            out[ch] += saw(midi(m), dur, detune=det, maxf=9000)[:n]
    t = np.arange(n) / SR
    env = np.minimum(1, t / 0.01) * np.clip((dur - t) / 0.05, 0, 1)
    out = np.vstack([filt(out[c], "lp", cutoff) for c in range(2)]) * env
    return out / (len(notes) * 3) * amp


def chop(m, dur=0.22, amp=1.0, vowel=(730, 1090)):
    t = tt(dur)
    s = saw(midi(m), dur, maxf=8000)
    s = filt(s, "bp", (vowel[0] * 0.8, vowel[0] * 1.2)) + 0.7 * filt(s, "bp", (vowel[1] * 0.85, vowel[1] * 1.15))
    return s * np.minimum(1, t / 0.01) * np.clip((dur - t) / 0.06, 0, 1) * amp * 0.9


def obass(m, dur, amp=1.0):
    t = tt(dur)
    f = midi(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t)
    return s * np.minimum(1, t / 0.004) * np.clip((dur - t) / 0.02, 0, 1) * np.exp(-t * 3) * amp * 0.5


def clap(amp=1.0):
    d = 0.25
    t = tt(d)
    env = np.zeros(len(t))
    for off in (0, 0.01, 0.022):
        i = int(off * SR); env[i:] += np.exp(-t[:len(t) - i] * 38)
    return filt(noise(d), "bp", (1000, 6500)) * env * amp * 0.45


def shaker(amp=1.0):
    d = 0.08
    t = tt(d)
    return filt(noise(d), "hp", 6500) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * amp * 0.3


def whoosh(dur=0.35, amp=1.0, up=True):
    t = tt(dur)
    s = sweep_filter(noise(dur), "bp", 700 if up else 6000, 6000 if up else 700)
    return s * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2 * amp * 0.55


def thump(amp=1.0):
    d = 0.3
    t = tt(d)
    body = np.sin(2 * np.pi * (70 + 60 * np.exp(-t * 40)) * t) * np.exp(-t * 18)
    paper = filt(noise(d), "bp", (800, 4000)) * np.exp(-t * 45) * 0.5
    return (body + paper) * amp * 0.9


def cabin_chime(amp=1.0):
    out = np.zeros(int(2.6 * SR))
    for k, (m, st) in enumerate(((88, 0.0), (84, 0.55))):
        t = tt(2.0)
        f = midi(m)
        s = (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t * 2.2) * np.minimum(1, t / 0.004)
        i = int(st * SR); out[i:i + len(s)] += s[:len(out) - i]
    return out * amp * 0.3


def engine(dur, amp=1.0):
    t = tt(dur)
    rise = np.clip((t - (dur - B(1.2))) / B(1.2), 0, 1) ** 2
    f = 95 * (1 + 1.5 * rise)
    hum = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + filt(noise(dur), "lp", 500) * 0.8
    jet = sweep_filter(noise(dur), "bp", 500, 3000) * (0.2 + 0.8 * rise) * 0.4
    return (hum + jet) * np.minimum(1, t / 0.6) * amp * 0.25


CH = {"F#m": (42, [61, 66, 69, 73]), "D": (38, [62, 66, 69, 74]), "A": (45, [61, 64, 69, 73]), "E": (40, [59, 64, 68, 71])}
PROG = ["F#m", "D", "A", "E"]
HOOK = {"F#m": [(0, 73), (1, 76), (2, 78), (3, 76), (4, 73), (6, 69), (7, 71)],
        "D": [(0, 74), (1, 78), (2, 81), (3, 78), (4, 76), (6, 74), (7, 73)],
        "A": [(0, 76), (1, 73), (2, 76), (3, 81), (4, 80), (5, 81), (6, 76)],
        "E": [(0, 80), (1, 76), (2, 71), (3, 76), (4, 80), (6, 83), (7, 80)]}


def bar(b, kick_on=True, hook=0.0, chops=0.0, saw_=0.0, shak16=False, bass_on=True, chords=0.9):
    t0 = b * BAR; name = PROG[b % 4]; root, notes = CH[name]
    for q in range(4):
        tb = t0 + q * BEAT
        if kick_on:
            place(music, tb, kick(0.8, 0.4, 46, 150), 1.0); kicks.append(tb)
            if q % 2: place(music, tb, clap(1.0), pan=0.05, rev=0.2)
            place(music, tb + E8, hat(0.5, open_=True), pan=0.3)
        for s in range(4 if shak16 else 2):
            place(music, tb + s * BEAT / (4 if shak16 else 2), shaker(0.8 if s % 2 == 0 else 0.5), pan=-0.3)
    for e in range(8):
        te = t0 + e * E8
        if bass_on and e % 2 == 1: place(music, te, obass(root + (12 if e % 4 == 3 else 0), E8 * 0.9), 1.0)
        if chords and e in (1, 3, 4, 6):
            for k, m in enumerate(notes): place(music, te, marimba(m, 0.4, chords * 0.45), pan=-0.35 + k * 0.23, rev=0.2)
    if saw_: place(music, t0, supersaw(notes, BAR, 4200, saw_), 1.0, rev=0.25)
    for e, m in HOOK[name]:
        if hook:
            place(music, t0 + e * E8, marimba(m + 12, 0.5, hook), pan=0.15, rev=0.3)
            if saw_: place(music, t0 + e * E8, marimba(m, 0.5, hook * 0.6), pan=-0.1, rev=0.3)
    if chops:
        for e, m in ((3, notes[-1] + 12), (7, notes[-2] + 12)):
            place(music, t0 + e * E8, chop(m, 0.2, chops), pan=0.2, rev=0.35)


# ---------------- intro (bars 0-1)
place(sfx, 0.05, cabin_chime(1.0), pan=0.1, rev=0.5)
place(sfx, 0.0, engine(B(8), 1.0))
for b in (0, 1):
    root, notes = CH[PROG[b % 4]]
    ch = np.sum([marimba(m, 0.4, 0.4) for m in notes], axis=0)
    for e in (1, 3, 4, 6):
        s = filt(ch, "lp", 900 + 2600 * b + 400 * e)
        place(music, b * BAR + e * E8, s, pan=0.0, rev=0.3)
    for s_ in range(4): place(music, b * BAR + s_ * BEAT + E8, shaker(0.5), pan=-0.3)
place(music, BAR, clap(0.6), rev=0.3); place(music, BAR + 2 * BEAT, clap(0.6), rev=0.3)
place(sfx, B(5), riser(B(3), 400, 9000, 0.8), rev=0.3)
place(sfx, C["dive"], whoosh(B(1), 1.4), rev=0.2)

# ---------------- groove (bars 2-7)
for b in range(2, 8): bar(b, hook=0.75 if b >= 4 else 0.5, chops=0.5 if b >= 4 else 0.0, shak16=b >= 6)
place(sfx, B(8), crash(2.0, 0.8), rev=0.4)
place(sfx, B(24), crash(1.5, 0.5), rev=0.3)

# ---------------- bar 8: three stabs, then silence
for i, bt in enumerate((32, 33, 34)):
    root, notes = CH[["A", "E", "F#m"][i]]
    place(sfx, B(bt), supersaw(notes, 0.35, 6000, 1.1) * np.exp(-np.arange(int(0.35 * SR)) / SR * 6), 1.0, rev=0.4)
    place(sfx, B(bt), kick(1.0, 0.4, 46, 150), 1.0); place(sfx, B(bt), clap(0.8), rev=0.3)
place(sfx, B(35), reverse_swell(BEAT, 0.9))

# ---------------- drop (bars 9-10)
for b in (9, 10): bar(b, hook=0.9, chops=0.8, saw_=0.8, shak16=True)
place(sfx, B(36), crash(2.4, 1.1), rev=0.5); place(sfx, B(36), boom(2.0), 0.7)

# ---------------- earth breakdown (bars 11-12)
for b in (11, 12):
    root, notes = CH[PROG[b % 4]]
    place(music, b * BAR, pad(notes, BAR, 1800, 0.3, 0.6), 0.6, rev=0.5)
    for e in range(8): place(music, b * BAR + e * E8, marimba(notes[e % 4] + 12, 0.45, 0.4), pan=(-0.3 if e % 2 else 0.3), rev=0.4)
    place(music, b * BAR, obass(root, BAR * 0.9, 0.8), 1.0)
place(sfx, B(48), riser(B(4), 300, 10000, 0.8), rev=0.3)
place(sfx, B(51.5), reverse_swell(B(0.5), 0.6))

# ---------------- logo (bars 13-14)
bar(13, hook=0.7, chops=0.5, saw_=0.5)
for q in range(2):
    tb = B(56 + q); place(music, tb, kick(0.95, 0.4, 46, 150), 1.0); kicks.append(tb)
place(sfx, B(52), crash(2.4, 0.9), rev=0.5); place(sfx, B(52), boom(1.8), 0.6)
fin = B(58)
root, notes = CH["A"]
place(sfx, fin, supersaw(notes + [76], 1.8, 5000, 0.9), 1.0, rev=0.5)
for k, m in enumerate([69, 73, 76, 81, 85]): place(music, fin + k * 0.05, marimba(m, 1.2, 0.5), pan=-0.3 + k * 0.15, rev=0.5)
place(sfx, C["cta"], cabin_chime(0.8)[:int(0.5 * SR)], pan=0.2, rev=0.4)

# ---------------- cuts and stamps
for c in C["cuts"]:
    if c < B(8) + 0.01: continue
    place(sfx, c - 0.18, whoosh(0.26, 0.55), pan=0.0)
for s in C["stamps"]:
    place(sfx, s, thump(0.9), pan=-0.3, rev=0.1)

# ---------------- mix
duck = np.ones(N)
for k in kicks:
    m = (tn >= k) & (tn < k + BEAT)
    duck[m] = np.minimum(duck[m], 0.45 + 0.55 * np.clip((tn[m] - k) / (BEAT * 0.55), 0, 1))
music *= duck
ir_len = int(1.5 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 7500), filt(rng.standard_normal(ir_len), "lp", 7500)]) * np.exp(-ti * 3.5)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.35
out = music * 0.8 + sfx * 0.75 + wet
gate = np.ones(N)
gate[(tn > B(35) + 0.02) & (tn < B(36) - 0.02)] = 0.15
gate = np.convolve(gate, np.ones(240) / 240, "same")
out = np.vstack([filt(out[c], "hp", 30) * gate for c in range(2)])
out *= np.clip((DUR - tn) / 0.4, 0, 1)
out = np.tanh(out / np.abs(out).max() * 2.2)
out = out / np.abs(out).max() * 10 ** (-0.8 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
for a, b_ in [(0, B(8)), (B(8), B(32)), (B(32), B(36)), (B(36), B(44)), (B(44), B(52)), (B(52), DUR)]:
    s_ = out[:, int(a * SR):int(b_ * SR)]
    print(round(a, 2), round(b_, 2), round(20 * np.log10(np.sqrt((s_ ** 2).mean()) + 1e-9), 1))
