"""128 BPM wa-EDM score for the AIチャレンジ365 beat trailer (30 s = 16 bars).

Intro (bars 0-1): filtered supersaw chords opening up, koto hook, hats, kick joins in bar 1.
Build (bar 2): snare roll speeding up, riser, taiko 8ths. Countdown (bar 3): three
huge stabs on beats 1-3, then a beat of silence with a reverse swell.
Drop (bars 4-11): four-on-the-floor kick, claps on 2 and 4, open hats on the off-beats,
sidechained supersaw chords, sub bass, koto lead in miyako-bushi, taiko fills every 4 bars,
a stab + taiko hit on every bar's downbeat (the kanji slam).
Build 2 (bars 12-13): stutter hats in 8ths then 16ths with the picture strobe, riser,
last beat silent. Final drop (bar 14): big hit, full groove. Logo (bar 15): hit,
two beats of groove, final hit and ring-out.
Usage: python3 beat_synth.py ../audio/synth.py ../wa/wa_synth.py cues.json out.wav
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
at = lambda b: b * BAR
kicks = []


def supersaw(notes, dur, cutoff=4000, amp=1.0):
    n = int(dur * SR)
    out = np.zeros((2, n))
    for m in notes:
        for det, ch in ((-14, 0), (-5, 1), (0, 0), (0, 1), (6, 0), (15, 1)):
            out[ch] += saw(midi(m), dur, detune=det, maxf=9000)[:n]
    t = np.arange(n) / SR
    env = np.minimum(1, t / 0.01) * np.clip((dur - t) / 0.05, 0, 1)
    out = np.vstack([filt(out[c], "lp", cutoff) for c in range(2)]) * env
    return out / (len(notes) * 3) * amp


def sub(m, dur, amp=1.0):
    t = tt(dur)
    return np.sin(2 * np.pi * midi(m) * t) * np.minimum(1, t / 0.005) * np.clip((dur - t) / 0.02, 0, 1) * amp * 0.8


def edm_kick(amp=1.0):
    d = 0.35
    t = tt(d)
    f = 48 + 110 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8)
    click = filt(noise(d), "hp", 3000) * np.exp(-t * 400) * 0.4
    return np.tanh((body + click) * 2.0) * amp


def clap(amp=1.0):
    d = 0.25
    t = tt(d)
    env = np.zeros(len(t))
    for off in (0, 0.01, 0.02):
        i = int(off * SR); env[i:] += np.exp(-t[:len(t) - i] * 45)
    return filt(noise(d), "bp", (900, 5000)) * env * amp * 0.45


def stab(notes, amp=1.0):
    return supersaw(notes, 0.35, 6000, amp) * np.exp(-np.arange(int(0.35 * SR)) / SR * 6)


def lead(m, dur, amp=1.0):
    return koto(m, dur + 0.4, amp, bright=0.8)


CH = {"Am": (45, [57, 60, 64, 69]), "F": (41, [57, 60, 65, 69]), "G": (43, [55, 59, 62, 67]), "Em": (40, [55, 59, 64, 67]), "Dm": (38, [57, 62, 65, 69])}
PROG = ["Am", "F", "G", "Em"]
HOOK = [76, 77, 81, 83, 81, 77, 76, 72]   # miyako-bushi flavour over A minor

def groove_bar(b, full=True, chords=True, lead_on=True):
    t0 = at(b); name = PROG[b % 4]; root, notes = CH[name]
    for beat in range(4):
        tb = t0 + beat * BEAT
        place(music, tb, edm_kick(1.0), 1.0); kicks.append(tb)
        if beat % 2 == 1: place(music, tb, clap(1.0), pan=0.05, rev=0.2)
        place(music, tb + BEAT / 2, hat(0.6, open_=True), pan=0.3)
        for s in (1, 3): place(music, tb + s * BEAT / 4, hat(0.35), pan=-0.3)
        if full:
            place(music, tb + BEAT / 2, sub(root - 12 + 24, BEAT / 2 * 0.9, 0.8), 1.0)
            place(music, tb, sub(root - 12 + 12, BEAT / 2 * 0.9, 0.9), 1.0)
    if chords:
        for e in range(8):   # off-beat pumping chords
            place(music, t0 + e * BEAT / 2 + BEAT / 4, supersaw(notes, BEAT / 4, 5000, 0.8), 1.0, rev=0.15)
    if lead_on:
        for e, m in enumerate(HOOK if b % 2 == 0 else HOOK[::-1]):
            place(music, t0 + e * BEAT / 2, lead(m, BEAT / 2, 0.55), pan=-0.25, rev=0.3)


# ---------------- intro
for b in (0, 1):
    root, notes = CH[PROG[b % 4]]
    ch = supersaw(notes, BAR, 900 if b == 0 else 2200, 0.9)
    place(music, at(b), ch, 1.0, rev=0.35)
    for e, m in enumerate(HOOK):
        place(music, at(b) + e * BEAT / 2, lead(m - (12 if b == 0 else 0), BEAT / 2, 0.6), pan=-0.2, rev=0.4)
    for s8 in range(8):
        place(music, at(b) + s8 * BEAT / 2, hat(0.3 if s8 % 2 else 0.2), pan=0.3)
    if b == 1:
        for beat in range(4): place(music, at(1) + beat * BEAT, edm_kick(0.8), 1.0); kicks.append(at(1) + beat * BEAT)
place(sfx, 0.0, odaiko(0.9), rev=0.4)
place(sfx, at(1), odaiko(1.0), rev=0.4)

# ---------------- build (bar 2)
root, notes = CH["F"]
place(music, at(2), supersaw(notes, BAR, 3000, 0.9), 1.0, rev=0.3)
for e in range(8): place(music, at(2) + e * BEAT / 2, odaiko(0.4 + 0.08 * e), 1.0)
tr = at(2)
while tr < at(3) - 0.02:
    place(music, tr, snare(0.3 + 0.6 * (tr - at(2)) / BAR), rev=0.15)
    tr += max(0.04, BEAT / 2 * (1 - (tr - at(2)) / BAR * 0.85))
place(sfx, at(2), riser(BAR, 300, 9000, 0.9), rev=0.3)
for i, w in enumerate(range(4)): place(sfx, at(2) + i * BEAT, hyoshigi(0.5), pan=0.3)

# ---------------- countdown (bar 3): three stabs, then silence
for i, tc in enumerate(C["countdown"]):
    place(sfx, tc, stab([57 + i * 2, 64 + i * 2, 69 + i * 2], 1.3), 1.0, rev=0.4)
    place(sfx, tc, odaiko(1.1), 1.0, rev=0.3)
    place(sfx, tc, boom(0.8), 0.6)
place(sfx, at(4) - BEAT, reverse_swell(BEAT, 1.0))

# ---------------- drop (bars 4-11)
for b in range(4, 12):
    groove_bar(b)
    place(sfx, at(b), stab(CH[PROG[b % 4]][1], 1.0), 1.0, rev=0.3)
    place(sfx, at(b), odaiko(1.0), 1.0, rev=0.3)
    if b in (7, 11):   # taiko fill on the last beat
        for s in range(4): place(music, at(b) + BEAT * 3 + s * BEAT / 4, shime(0.6 + 0.1 * s), pan=0.2)
for h in (at(4), at(8)):
    place(sfx, h, crash(2.0, 1.0), rev=0.4); place(sfx, h, boom(2.0), 0.9)

# ---------------- build 2 (bars 12-13): stutter + riser
for b in (12, 13):
    root, notes = CH[PROG[b % 4]]
    place(music, at(b), supersaw(notes, BAR, 1500 if b == 12 else 4000, 0.8), 1.0, rev=0.3)
    step = BEAT / (2 if b == 12 else 4)
    k = 0
    while k * step < BAR - (BEAT if b == 13 else 0) - 1e-6:
        place(music, at(b) + k * step, hat(0.5, open_=False), pan=(-0.3 if k % 2 else 0.3))
        place(music, at(b) + k * step, shime(0.25 + 0.3 * (b - 12)), pan=0.1)
        k += 1
place(sfx, at(12), riser(BAR * 2 - BEAT, 250, 11000, 1.0), rev=0.3)
place(sfx, at(14) - BEAT * 0.9, reverse_swell(BEAT * 0.9, 1.0))

# ---------------- final drop (bar 14) and logo (bar 15)
groove_bar(14)
place(sfx, at(14), crash(2.0, 1.1), rev=0.5); place(sfx, at(14), boom(2.4), 1.1); place(sfx, at(14), odaiko(1.5), 1.0, rev=0.4)
place(sfx, at(14) + BEAT * 2, odaiko(1.3), 1.0, rev=0.4)
for beat in range(2):
    tb = at(15) + beat * BEAT
    place(music, tb, edm_kick(1.0), 1.0); kicks.append(tb)
place(music, at(15), supersaw(CH["Am"][1] + [76], BEAT * 2, 5000, 0.9), 1.0, rev=0.4)
place(sfx, at(15), odaiko(1.4), 1.0, rev=0.5); place(sfx, at(15), crash(2.0, 0.8), rev=0.5)
fin = at(15) + BEAT * 3
place(sfx, fin, stab([45, 57, 64, 69, 72], 1.5), 1.0, rev=0.6)
place(sfx, fin, odaiko(1.6), 1.0, rev=0.6); place(sfx, fin, boom(2.0), 1.0)
for k, m in enumerate([69, 72, 76, 81]):
    place(music, fin + k * 0.05, koto(m, 1.6, 0.5), pan=-0.3 + k * 0.2, rev=0.5)

# ---------------- mix
tn = np.arange(N) / SR
duck = np.ones(N)
for k in kicks:
    m = (tn >= k) & (tn < k + BEAT)
    duck[m] = np.minimum(duck[m], 0.35 + 0.65 * np.clip((tn[m] - k) / (BEAT * 0.6), 0, 1))
music *= duck
ir_len = int(1.8 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 7000), filt(rng.standard_normal(ir_len), "lp", 7000)]) * np.exp(-ti * 3)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.4
out = music * 0.8 + sfx * 0.85 + wet
gate = np.ones(N)
gate[(tn > at(4) - BEAT + 0.02) & (tn < at(4) - 0.02)] = 0.12   # the breath after the countdown
gate[(tn > at(14) - BEAT + 0.02) & (tn < at(14) - 0.02)] = 0.12
gate = np.convolve(gate, np.ones(240) / 240, "same")
out = np.vstack([filt(out[c], "hp", 30) * gate for c in range(2)])
out *= np.clip((DUR - tn) / 0.4, 0, 1)
out = np.tanh(out / np.abs(out).max() * 1.8)
out = out / np.abs(out).max() * 10 ** (-0.8 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
for a, b_ in [(0, at(2)), (at(2), at(4)), (at(4), at(12)), (at(12), at(14)), (at(14), DUR)]:
    s_ = out[:, int(a * SR):int(b_ * SR)]
    print(round(a, 2), round(b_, 2), round(20 * np.log10(np.sqrt((s_ ** 2).mean()) + 1e-9), 1))
