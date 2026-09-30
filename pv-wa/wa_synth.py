"""70 BPM wa-modern score for the 和 PV.

Koto (Karplus-Strong string with oshide bends), shakuhachi (breathy tone
with vibrato and meri bends), shō cluster, taiko (ōdaiko, shime, rim),
hyoshigi, suzu, water drop and shishi-odoshi, in the miyako-bushi scale.
Every effect is placed on the cue times the page exports.
Usage: python3 wa_synth.py ../audio/synth.py cues.json out.wav
"""
import sys

import numpy as np

base_src, cues_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(base_src).read()
src = src[:src.index("# ---------------------------------------------------------------- instruments")]
src = src.replace("DUR = 13.5", "DUR = 30.0")
sys.argv = [base_src, cues_path, out_path]
exec(src)

C = cues
BEAT = 60 / C["bpm"]
BAR = BEAT * 4
T0 = C["t0"]
# miyako-bushi on E: E F A B C
MIYAKO = [52, 53, 57, 59, 60, 64, 65, 69, 71, 72, 76, 77, 81, 83, 84]


# ---------------------------------------------------------------- instruments
def koto(m, dur=2.2, amp=1.0, bend=0.0, bright=0.5):
    """Plucked string (Karplus-Strong), optional oshide bend after the attack."""
    f = midi(m)
    L = int(SR / f)
    n = int(dur * SR)
    y = np.zeros(n + L)
    exc = rng.uniform(-1, 1, L)
    exc = np.convolve(exc, np.ones(3) / 3, "same") * (1 - bright) + exc * bright
    y[:L] = exc
    damp = 0.996
    i = L
    while i < n + L:
        j = min(i + L, n + L)
        seg_ = y[i - L:j - L]
        prev = y[i - L - 1:j - L - 1] if i - L - 1 >= 0 else np.concatenate([[0], y[i - L:j - L - 1]])
        y[i:j] = damp * 0.5 * (seg_ + prev[:len(seg_)])
        i = j
    y = y[L:]
    if bend:
        t = np.arange(n) / SR
        ratio = 2 ** (bend * np.clip((t - 0.18) / 0.25, 0, 1) / 12)
        pos = np.cumsum(ratio)
        pos = np.clip(pos, 0, n - 1)
        y = np.interp(pos, np.arange(n), y)
    body = filt(y, "lp", 5000) + 0.25 * filt(y, "bp", (180, 400))
    t = np.arange(n) / SR
    return body * np.exp(-t * 0.6) * amp * 0.6


def shakuhachi(m, dur, amp=1.0, bend_from=-1.0):
    t = tt(dur)
    f0 = midi(m)
    pitch = f0 * 2 ** ((bend_from * np.exp(-t * 6)) / 12)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.4) / 0.5, 0, 1)
    ph = 2 * np.pi * np.cumsum(pitch * vib) / SR
    tone = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    breath = filt(noise(dur), "bp", (f0 * 0.8, f0 * 3.5)) * 0.45
    burst = filt(noise(dur), "bp", (800, 4000)) * np.exp(-t * 18) * 0.8   # muraiki: a puff of air on the attack
    env = np.minimum(1, t / 0.12) * np.clip((dur - t) / 0.35, 0, 1)
    swell = 0.75 + 0.25 * np.sin(np.pi * np.clip(t / dur, 0, 1))
    return (tone * 0.6 + breath + burst) * env * swell * amp * 0.45


def sho(notes, dur, amp=1.0):
    t = tt(dur)
    out = np.zeros((2, len(t)))
    for i, m in enumerate(notes):
        f = midi(m)
        for det, ch in ((-2.5, 0), (2.5, 1)):
            ff = f * 2 ** (det / 1200)
            s = np.sin(2 * np.pi * ff * t) + 0.3 * np.sin(4 * np.pi * ff * t) + 0.12 * np.sin(6 * np.pi * ff * t)
            out[ch] += s
    env = np.minimum(1, t / 1.2) * np.clip((dur - t) / 1.0, 0, 1)
    return out * env / len(notes) * amp * 0.35


def odaiko(amp=1.0):
    d = 1.4
    t = tt(d)
    f = 52 + 38 * np.exp(-t * 14)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    skin = filt(noise(d), "lp", 900) * np.exp(-t * 9) * 0.6
    slap = filt(noise(d), "bp", (300, 1500)) * np.exp(-t * 60) * 0.5
    return np.tanh((body + skin + slap) * 1.5) * amp


def shime(amp=1.0):
    d = 0.25
    t = tt(d)
    f = 320 + 140 * np.exp(-t * 60)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28)
    return (s + filt(noise(d), "bp", (1500, 5000)) * np.exp(-t * 70) * 0.5) * amp * 0.5


def ka(amp=1.0):
    d = 0.08
    t = tt(d)
    return (np.sin(2 * np.pi * 1450 * t) + np.sin(2 * np.pi * 2310 * t) * 0.6) * np.exp(-t * 90) * amp * 0.35


def hyoshigi(amp=1.0):
    d = 0.5
    t = tt(d)
    out = np.zeros(len(t))
    for off, a in ((0, 1), (0.11, 0.85)):
        i = int(off * SR)
        tk = t[:len(t) - i]
        out[i:] += (np.sin(2 * np.pi * 2250 * tk) + 0.7 * np.sin(2 * np.pi * 3120 * tk) + 0.4 * np.sin(2 * np.pi * 5100 * tk)) * np.exp(-tk * 38) * a
    return out * amp * 0.45


def suzu(dur=0.7, amp=1.0, density=40):
    n = int(dur * SR)
    out = np.zeros(n)
    for _ in range(int(density * dur)):
        s = int(rng.uniform(0, dur * 0.8) * SR)
        f = rng.uniform(4200, 7800)
        t = np.arange(int(0.25 * SR)) / SR
        b_ = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.53 * t)) * np.exp(-t * 22) * rng.uniform(0.3, 1)
        e = min(n, s + len(b_))
        out[s:e] += b_[:e - s]
    return out * amp * 0.12


def water_drop(amp=1.0):
    d = 0.3
    t = tt(d)
    f = 700 + 1500 * (1 - np.exp(-t * 40))
    bloop = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)
    splash = filt(noise(d), "hp", 3000) * np.exp(-t * 50) * 0.3
    return (bloop + splash) * amp * 0.6


def shishi_odoshi(amp=1.0):
    d = 0.9
    t = tt(d)
    knock = filt(noise(d), "bp", (500, 700)) * np.exp(-t * 12) * 3 + filt(noise(d), "bp", (1050, 1300)) * np.exp(-t * 16) * 2
    tone = np.sin(2 * np.pi * 610 * t) * np.exp(-t * 9) + 0.5 * np.sin(2 * np.pi * 1180 * t) * np.exp(-t * 14)
    return (knock * 0.4 + tone) * np.minimum(1, t / 0.002) * amp * 0.5


def brush_swish(dur=0.3, amp=1.0):
    t = tt(dur)
    return sweep_filter(noise(dur), "bp", 1500, 4500) * np.sin(np.pi * t / dur) ** 1.2 * amp * 0.25


def stamp(amp=1.0):
    d = 0.3
    t = tt(d)
    return (np.sin(2 * np.pi * 95 * t) * np.exp(-t * 30) + filt(noise(d), "lp", 1500) * np.exp(-t * 40) * 0.5) * amp


def shoji(dur=0.7):
    t = tt(dur)
    rub = filt(noise(dur), "bp", (200, 1400)) * (0.7 + 0.3 * np.sin(2 * np.pi * 13 * t))
    out = rub * np.sin(np.pi * t / dur) ** 0.8 * 0.5
    thud = stamp(0.25)[:int(0.05 * SR)]
    out[len(out) - len(thud):] += thud   # the panels knock at the end of their travel
    return out


def fan(dur=0.7):
    t = tt(dur)
    swish = sweep_filter(noise(dur), "bp", 800, 6000) * np.sin(np.pi * t / dur) ** 2 * 0.5
    ticks = np.zeros(len(t))
    for i in range(13):
        p = int((0.08 + i * 0.035) * SR)
        ticks[p:p + 200] += np.sin(2 * np.pi * 3500 * np.arange(200) / SR) * np.exp(-np.arange(200) / 30) * 0.4
    return swish + ticks


def noren(dur=0.7):
    t = tt(dur)
    return filt(noise(dur), "bp", (300, 2500)) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 11 * t))) * np.sin(np.pi * t / dur) ** 1.5 * 0.45


def scroll(dur=0.7):
    t = tt(dur)
    rustle = filt(noise(dur), "bp", (1500, 6000)) * (0.5 + 0.5 * (rng.random(len(t)) > 0.97)) * 0.5
    roll = filt(noise(dur), "lp", 300) * 0.6
    return (rustle + roll) * np.sin(np.pi * t / dur) ** 1.2


# ---------------------------------------------------------------- arrangement
imp = C["impact"]
place(sfx, 0.0, sweep_filter(noise(imp), "bp", 3000, 900) * np.linspace(0, 1, int(imp * SR)) ** 2 * 0.25)
place(sfx, imp, water_drop(1.0), rev=0.4)
place(sfx, imp, odaiko(0.55), 1.0, rev=0.3)
place(music, imp + 0.02, koto(52, 3.0, 0.9), pan=-0.1, rev=0.5)
place(music, 0.5, sho([69, 71, 76, 81], BAR * 2 - 0.5, 0.6), 1.0, rev=0.4)
place(music, 1.5, koto(57, 2.5, 0.8, bend=1), pan=0.2, rev=0.5)
place(sfx, 1.5, brush_swish(0.7, 0.9), pan=0.1)

# the sentence: a brush stroke and a koto note per character
for i, tc in enumerate(C["sentence"]):
    place(sfx, tc, brush_swish(0.28, 0.6), pan=0.35)
    place(music, tc, koto(MIYAKO[5 + i], 1.8, 0.55, bright=0.7), pan=0.25 - i * 0.05, rev=0.4)
place(sfx, C["stamp"], hyoshigi(1.0), pan=0.1, rev=0.35)
place(sfx, C["stamp"], stamp(0.7))

# works: a slow groove under the four reveals
w0 = T0["works"]
riff = [64, 69, 71, 72, 71, 69, 64, 65]
for bar in range(2):
    t0 = w0 + bar * BAR
    place(music, t0, odaiko(0.6), 1.0, rev=0.25)
    for b8 in range(8):
        tb = t0 + b8 * BEAT / 2
        place(music, tb, shime(0.5 if b8 % 2 == 0 else 0.28), pan=0.35)
        place(music, tb, koto(riff[b8] - 12 * (b8 % 4 == 0), 1.0, 0.35, bright=0.4), pan=-0.3, rev=0.25)
    place(music, t0, sho([57, 64, 69, 71], BAR, 0.4), 1.0, rev=0.3)
for w in C["works"]:
    fx = {"shoji": shoji, "fan": fan, "noren": noren, "scroll": scroll}[w["reveal"]]
    place(sfx, w["t"] + 0.05, fx(0.7), pan=0.1, rev=0.2)

# interlude: shakuhachi over the shō, gold leaf in the bells
i0 = T0["interlude"]
place(music, i0, sho([69, 71, 76, 78, 81], BAR + 0.8, 0.35), 1.0, rev=0.5)
phrase = [(69, 0.2, 1.1, -1.5), (71, 1.35, 0.7, -1), (72, 2.1, 0.5, 0), (71, 2.6, 1.2, -1)]
for m, st, d, bf in phrase:
    place(music, i0 + st, shakuhachi(m, d, 0.55, bf), pan=-0.15, rev=0.6)
for k in range(9):
    place(sfx, i0 + 0.3 + k * 0.37, suzu(0.3, 0.35, 12), pan=rng.uniform(-0.6, 0.6), rev=0.5)

# grid: taiko groove, every flip plucks the next note of the melody
g0 = T0["grid"]
for bar in range(2):
    t0 = g0 + bar * BAR
    for beat in range(4):
        tb = t0 + beat * BEAT
        if beat in (0, 2):
            place(music, tb, odaiko(0.85), 1.0, rev=0.25)
        for s in range(4):
            if (beat * 4 + s) % 3 != 1:
                place(music, tb + s * BEAT / 4, shime(0.35 + 0.2 * (s == 0)), pan=0.3)
        place(music, tb + BEAT / 2, ka(0.7), pan=-0.35)
    place(music, t0, sho([57, 64, 69, 72], BAR, 0.45), 1.0, rev=0.3)
flip_mel = [69, 72, 71, 76, 77, 76, 72, 71]
for i, tf in enumerate(C["flips"]):
    if i < 8:
        place(music, tf, koto(flip_mel[i], 1.4, 0.6, bend=(1 if i in (3, 6) else 0), bright=0.7), pan=(-0.4 if i % 2 else 0.4), rev=0.3)
red = C["flips"][8]
for k, m in enumerate(MIYAKO[3:14]):
    place(music, red + k * 0.035, koto(m, 1.6, 0.35, bright=0.8), pan=-0.5 + k * 0.1, rev=0.4)   # sukui glissando
roll_t = T0["logo"] - BEAT * 1.2
while roll_t < T0["logo"] - 0.03:
    place(music, roll_t, shime(0.2 + 0.6 * (roll_t - (T0["logo"] - BEAT * 1.2)) / (BEAT * 1.2)), pan=0.1)
    roll_t += 0.055

# signature: the big drum, the ensō, the stamp and the bamboo
l0 = T0["logo"]
place(sfx, l0, odaiko(1.3), 1.0, rev=0.5)
place(music, l0, sho([69, 71, 76, 81, 83], DUR - l0, 0.8), 1.0, rev=0.5)
a, z = C["enso"]
place(sfx, a, brush_swish(z - a, 1.0), pan=-0.2, rev=0.2)
for k, m in enumerate([64, 69, 71, 76]):
    place(music, l0 + 1.1 + k * 0.06, koto(m, 2.4, 0.5), pan=-0.3 + k * 0.2, rev=0.5)
place(sfx, C["seal"], shishi_odoshi(1.0), pan=0.3, rev=0.5)
place(sfx, C["seal"], stamp(0.6))
place(sfx, T0["contact"] + 0.05, suzu(0.8, 0.9, 50), pan=0.2, rev=0.5)
for k, m in enumerate([84, 81, 77, 76, 72, 69, 65, 64]):
    place(music, T0["contact"] + 0.4 + k * 0.16, koto(m, 2.0, 0.35, bright=0.6), pan=0.4 - k * 0.1, rev=0.5)

# ---------------------------------------------------------------- mix
tn = np.arange(N) / SR
ir_len = int(3.6 * SR)
ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 5000), filt(rng.standard_normal(ir_len), "lp", 5000)]) * np.exp(-ti * 1.7)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.55
out = music * 0.8 + sfx * 0.85 + wet
out = np.vstack([filt(out[c], "hp", 30) for c in range(2)])
fade = np.clip((DUR - tn) / 1.2, 0, 1)
out *= fade
out = np.tanh(out / np.abs(out).max() * 1.4)
out = out / np.abs(out).max() * 10 ** (-1 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
print("peak", 20 * np.log10(np.abs(out).max()), "rms", 20 * np.log10(np.sqrt((out ** 2).mean())))
