"""90 BPM lo-fi soundtrack for the editorial PV.

Electric piano (FM) on jazz voicings, swung drums, sub bass, vinyl crackle,
tape wow/flutter and a tape stop at the end. Sound effects are musical:
kalimba notes for vertical type, marimba for grid plates, film shutter,
page swooshes and a pen stroke for the monogram.
Borrows the bus/filter helpers from the intro soundtrack (synth.py).
Usage: python3 lofi.py ../audio/synth.py cues.json out.wav
"""
import sys

import numpy as np

base_src, cues_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(base_src).read()
src = src[:src.index("# ---------------------------------------------------------------- instruments")]
src = src.replace("DUR = 13.5", "DUR = 30.0")
sys.argv = [base_src, cues_path, out_path]
exec(src)  # SR, N, music/sfx/rev_send buses, place(), filt(), sweep_filter(), noise(), midi(), tt(), rng, cues

C = cues
BEAT = 60 / C["bpm"]
BAR = BEAT * 4
T0 = C["t0"]
SWING = 0.62  # position of the off-beat 8th inside a beat


# ---------------------------------------------------------------- instruments
def ep(m, dur, vel=1.0):
    """FM electric piano: soft bark on the attack, bell-like tine, slow decay."""
    f = midi(m)
    t = tt(dur + 0.6)
    idx = 2.0 * np.exp(-t * 3.2) * vel + 0.25
    body = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    tine = np.sin(2 * np.pi * f * 14 * t) * np.exp(-t * 28) * 0.18 * vel
    env = np.exp(-t * 0.9) * np.minimum(1, t / 0.004)
    rel = np.clip((dur + 0.6 - t) / 0.6, 0, 1)
    return (body + tine) * env * rel * 0.32 * vel


def chord(notes, dur, vel=1.0, strum=0.0, pan_spread=0.5):
    """Stereo chord with a gentle tremolo that moves across the field."""
    n = int((dur + 0.6 + strum * len(notes)) * SR)
    out = np.zeros((2, n))
    for i, m in enumerate(notes):
        s = ep(m, dur, vel * (0.85 + 0.15 * rng.random()))
        p = (i / max(len(notes) - 1, 1) - 0.5) * pan_spread
        a = (p + 1) * np.pi / 4
        o = int(i * strum * SR)
        out[0, o:o + len(s)] += s * np.cos(a) * np.sqrt(2)
        out[1, o:o + len(s)] += s * np.sin(a) * np.sqrt(2)
    tn = np.arange(n) / SR
    trem = 0.12 * np.sin(2 * np.pi * 4.2 * tn)
    out[0] *= 1 + trem
    out[1] *= 1 - trem
    return out


def lofi_kick(amp=1.0):
    d = 0.4
    t = tt(d)
    f = 42 + 26 * np.exp(-t * 30)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    click = filt(noise(d), "bp", (900, 2500)) * np.exp(-t * 400) * 0.15
    return filt(np.tanh((s + click) * 1.3), "lp", 3000) * amp


def snap(amp=1.0):
    d = 0.25
    t = tt(d)
    crack = filt(noise(d), "bp", (1800, 4200)) * np.exp(-t * 45)
    body = filt(noise(d), "bp", (600, 1500)) * np.exp(-t * 25) * 0.4
    return (crack + body) * amp * 0.8


def hat(amp=1.0):
    d = 0.08
    t = tt(d)
    return filt(noise(d), "hp", 6500) * np.exp(-t * 55) * amp * 0.5


def shaker(amp=1.0):
    d = 0.12
    t = tt(d)
    e = np.minimum(1, t / 0.03) * np.exp(-t * 30)
    return filt(noise(d), "bp", (4500, 9000)) * e * amp * 0.45


def rim(amp=1.0):
    d = 0.1
    t = tt(d)
    return (np.sin(2 * np.pi * 1700 * t) * 0.5 + filt(noise(d), "bp", (2000, 5000))) * np.exp(-t * 60) * amp * 0.5


def sub_bass(m, dur, amp=1.0):
    f = midi(m)
    t = tt(dur)
    s = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t)
    e = np.minimum(1, t / 0.01) * np.clip((dur - t) / 0.06, 0, 1) * np.exp(-t * 0.8)
    return np.tanh(s * 1.2) * e * amp * 0.6


def kalimba(m, amp=1.0):
    f = midi(m)
    d = 1.4
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 3.5) + 0.35 * np.sin(2 * np.pi * f * 5.93 * t) * np.exp(-t * 18)
    return s * np.minimum(1, t / 0.002) * amp * 0.35


def marimba(m, amp=1.0):
    f = midi(m)
    d = 1.0
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 6) + 0.4 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 22)
    return s * np.minimum(1, t / 0.002) * amp * 0.4


def felt(m, amp=1.0, dur=2.0):
    f = midi(m)
    t = tt(dur)
    s = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.6 for k in (1, 2, 3, 4))
    return filt(s * np.exp(-t * 1.2) * np.minimum(1, t / 0.008), "lp", 2600) * amp * 0.35


def shutter(amp=1.0):
    """Film camera: mirror slap, a short whirr, the second curtain."""
    d = 0.16
    t = tt(d)
    out = np.zeros(len(t))
    for off, a in ((0, 1.0), (0.045, 0.7)):
        i = int(off * SR)
        tk = t[:len(t) - i]
        out[i:] += filt(noise(len(tk) / SR), "bp", (1800, 6500)) * np.exp(-tk * 260) * a
    whirr = filt(noise(d), "bp", (300, 1200)) * np.exp(-((t - 0.03) / 0.02) ** 2) * 0.3
    return (out + whirr) * amp


def page(amp=1.0, dur=0.38):
    t = tt(dur)
    s = sweep_filter(noise(dur), "bp", 700, 3200) * np.sin(np.pi * t / dur) ** 1.5
    return s * amp * 0.5


def pen(dur, amp=1.0):
    t = tt(dur)
    grit = filt(noise(dur), "bp", (2800, 7500))
    bumps = 0.6 + 0.4 * np.sin(2 * np.pi * 9 * t + 3 * np.sin(2 * np.pi * 1.3 * t))
    return grit * bumps * np.sin(np.pi * t / dur) ** 0.6 * amp * 0.25


def soft_swell(dur, amp=1.0):
    t = tt(dur)
    n = np.vstack([filt(noise(dur), "bp", (2500, 9000)), filt(noise(dur), "bp", (2500, 9000))])
    return n * (t / dur) ** 3 * amp * 0.35


def air(dur, amp=1.0):
    t = tt(dur)
    n = np.vstack([filt(noise(dur), "bp", (5000, 12000)), filt(noise(dur), "bp", (5000, 12000))])
    return n * np.sin(np.pi * t / dur) ** 2 * amp * 0.025


# ---------------------------------------------------------------- harmony
V = {
    "Fmaj9": (41, [57, 60, 64, 67]),
    "Em7": (40, [55, 59, 62, 64]),
    "Dm9": (38, [53, 57, 60, 64]),
    "G13": (43, [53, 59, 64, 69]),
    "Cmaj9": (36, [52, 55, 59, 62]),
}
PROG = ["Fmaj9", "Em7", "Dm9", "G13", "Fmaj9", "Em7", "Dm9", "G13", "Fmaj9", "Cmaj9", "Fmaj9"]
PENTA = [69, 72, 74, 76, 79, 81, 84]
kick_times = []


def bar_t(i):
    return i * BAR


def groove(bar, kick=True, snare=True, hats=True, full_bass=True, perc=False, half=False):
    t0 = bar_t(bar)
    root, _ = V[PROG[bar]]
    for beat in range(4):
        tb = t0 + beat * BEAT
        off = tb + SWING * BEAT
        if kick and (beat in (0, 2) if not half else beat == 0):
            place(music, tb + 0.005, lofi_kick(0.95), 1.0)
            kick_times.append(tb)
        if kick and not half and beat == 2:
            place(music, off, lofi_kick(0.55), 1.0)
        if snare and ((beat in (1, 3)) if not half else beat == 2):
            place(music, tb + 0.012, snap(0.9), pan=0.05, rev=0.25)
        if hats:
            place(music, tb, hat(0.5 + 0.2 * rng.random()), pan=0.3)
            place(music, off, hat(0.3 + 0.2 * rng.random()), pan=0.3)
        if perc:
            place(music, off, rim(0.35), pan=-0.4, rev=0.15)
    if full_bass:
        place(music, t0, sub_bass(root, BEAT * 1.6), 1.0)
        place(music, t0 + 2 * BEAT + SWING * BEAT, sub_bass(root + 7 if bar % 2 else root + 12, BEAT * 0.9), 0.8)
        place(music, t0 + 3 * BEAT + SWING * BEAT, sub_bass(root, BEAT * 0.7), 0.7)


def comp(bar, vel=0.9):
    t0 = bar_t(bar)
    _, notes = V[PROG[bar]]
    place(music, t0 + 0.01, chord(notes, BEAT * 1.6, vel, strum=0.012), 0.8, rev=0.3)
    place(music, t0 + BEAT + SWING * BEAT, chord(notes, BEAT * 0.45, vel * 0.7, strum=0.006), 0.65, rev=0.25)
    if bar % 2:
        place(music, t0 + 3 * BEAT, chord(notes, BEAT * 0.8, vel * 0.6), 0.6, rev=0.3)


# ---------------------------------------------------------------- arrangement
# bar 0: the glyph. Chord swells through an opening filter.
root, notes = V[PROG[0]]
intro = chord(notes, BAR * 0.95, 0.8, strum=0.05)
intro = np.vstack([sweep_filter(intro[c], "lp", 350, 3500) for c in range(2)])
place(music, 0.05, intro, 1.0, rev=0.5)
place(sfx, 0.12, felt(81, 0.5), pan=0.25, rev=0.6)
place(sfx, BAR - 0.75, soft_swell(0.75, 0.8))

# bar 1: sentence + iris. Groove enters.
groove(1, perc=False)
comp(1)
place(sfx, 3.1, pen(0.9, 0.6), pan=-0.1)                      # the rule draws
place(sfx, T0["iris"], page(0.6, 0.66), rev=0.2)
# bars 2-3: four spreads
for bar in (2, 3):
    groove(bar, perc=True)
    comp(bar)
for i, ts in enumerate(C["spreads"]):
    place(sfx, ts, shutter(0.55), pan=0.2, rev=0.12)
    if i < 3:
        place(sfx, ts + 2 * BEAT - 0.36, page(0.55), pan=-0.2)
    place(sfx, ts + 0.1, kalimba(PENTA[[2, 4, 3, 5][i]], 0.5), pan=0.35, rev=0.4)

# bars 4-5: interlude. Drums thin out to shaker and rim; the text types itself in kalimba.
for bar in (4, 5):
    t0 = bar_t(bar)
    _, notes = V[PROG[bar]]
    place(music, t0, chord(notes, BAR * 0.95, 0.7, strum=0.04), 0.5, rev=0.55)
    place(music, t0, sub_bass(V[PROG[bar]][0], BAR * 0.9, 0.8), 0.6)
    for s16 in range(16):
        tb = t0 + (s16 // 2) * (BEAT / 2) + (SWING - 0.5) * BEAT * (s16 % 2)
        place(music, t0 + s16 * BEAT / 4 + (0.03 if s16 % 2 else 0), shaker(0.3 if s16 % 4 == 0 else 0.18), pan=-0.3)
    place(music, t0 + 3 * BEAT + 0.01, rim(0.4), pan=0.3, rev=0.3)
p0 = T0["pause"]
for i in range(7):
    place(sfx, p0 + 0.5 + i * 0.12, kalimba(PENTA[i % 7], 0.45), pan=0.3, rev=0.5)
for i in range(7):
    place(sfx, p0 + 1.6 + i * 0.12, kalimba(PENTA[(6 - i) % 7] - 12, 0.45), pan=-0.3, rev=0.5)
place(sfx, p0 + 1.2, air(T0["grid"] - p0 - 1.4, 1.0))
place(sfx, T0["grid"] - 0.75, soft_swell(0.75, 0.9))

# bars 6-7: grid. Groove returns with percussion; every plate plays a marimba note.
for bar in (6, 7):
    groove(bar, perc=True)
    comp(bar)
mel = [74, 76, 79, 81, 79, 84]
for i, tg in enumerate(C["grid"]):
    if i < 6:
        place(sfx, tg, marimba(mel[i], 0.6), pan=(-0.3 if i % 2 else 0.3), rev=0.3)
        place(sfx, tg, page(0.25, 0.3), pan=(0.3 if i % 2 else -0.3))
    else:
        _, notes = V["Cmaj9"]
        place(sfx, tg, chord([n + 12 for n in notes[:3]], 0.4, 0.6), 0.5, rev=0.4)
for r in range(3):
    place(sfx, C["gridOut"] + r * 0.08, page(0.45, 0.45), pan=(-0.5 + r * 0.5))

# bars 8-9: signature. Half-time; the pen draws the circle, a chime lands on the k.
for bar in (8, 9):
    groove(bar, hats=True, half=True, perc=False)
    t0 = bar_t(bar)
    _, notes = V[PROG[bar]]
    place(music, t0 + 0.01, chord(notes, BAR * 0.9, 0.85, strum=0.03), 0.85, rev=0.45)
lg = T0["logo"]
place(sfx, lg + 0.1, pen(1.2, 0.8), pan=0.1)
for m, dt in ((81, 0), (88, 0.05)):
    place(sfx, lg + 0.8 + dt, felt(m, 0.55), pan=0.2, rev=0.6)
place(sfx, lg + 1.4, felt(69, 0.4, 2.5), rev=0.5)
for i in range(9):
    place(sfx, lg + 2.0 + i * 0.08, kalimba(PENTA[(i + 2) % 7] + 12, 0.18), pan=0.5, rev=0.5)

# bar 10: contact, final chord, tape stop
_, notes = V[PROG[10]]
place(music, bar_t(10) + 0.01, chord(notes + [72], BAR * 1.1, 0.9, strum=0.06), 0.9, rev=0.6)
place(music, bar_t(10), sub_bass(V[PROG[10]][0], BAR, 0.9), 1.0)
place(sfx, T0["contact"] + 0.4, felt(76, 0.35), rev=0.6)

# ---------------------------------------------------------------- mix
duck = np.ones(N)
tn = np.arange(N) / SR
for k in kick_times:
    m = tn >= k
    duck[m] -= 0.25 * np.exp(-(tn[m] - k) * 8)
music *= np.clip(duck, 0.6, 1)

ir_len = int(3.0 * SR)
ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 4000), filt(rng.standard_normal(ir_len), "lp", 4000)]) * np.exp(-ti * 2.0)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.45

mixed = music * 0.75 + sfx * 0.85 + wet
mixed = np.vstack([filt(filt(mixed[c], "hp", 35), "lp", 11000) for c in range(2)])

# tape wow and flutter
warp = tn + 0.0014 * np.sin(2 * np.pi * 0.55 * tn) + 0.00025 * np.sin(2 * np.pi * 6.5 * tn)
mixed = np.vstack([np.interp(warp, tn, mixed[c]) for c in range(2)])

# tape stop: playback slows to a halt
ts, tl = 28.45, 0.75
pos = tn.copy()
m = tn > ts
dt = tn[m] - ts
pos[m] = ts + np.where(dt < tl, dt - dt ** 2 / (2 * tl), tl / 2)
stopped = np.vstack([np.interp(pos, tn, mixed[c]) for c in range(2)])
stopped[:, tn > ts + tl] = 0
stopped *= np.clip((ts + tl - tn) / 0.05, 0, 1) * (tn > ts) + (tn <= ts)

# vinyl crackle and hiss run underneath everything, including the tail
crackle = np.zeros(N)
nclicks = int(DUR * 7)
pos_c = rng.integers(0, N - 50, nclicks)
for p in pos_c:
    crackle[p:p + 30] += rng.standard_normal(30) * np.exp(-np.arange(30) / 6) * rng.uniform(0.05, 0.35)
crackle = filt(crackle, "hp", 1200)
hiss = filt(rng.standard_normal(N), "lp", 5000) * 0.006
vinyl = np.vstack([crackle + hiss, np.roll(crackle, 400) + hiss]) * 0.5
fade = np.clip((DUR - tn) / 0.8, 0, 1) * np.clip(tn / 0.05, 0, 1)
out = (stopped + vinyl) * fade

out = np.tanh(out / np.abs(out).max() * 1.3)
out = out / np.abs(out).max() * 10 ** (-1 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
print("peak", 20 * np.log10(np.abs(out).max()), "rms", 20 * np.log10(np.sqrt((out ** 2).mean())))
