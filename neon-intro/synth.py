"""Synthesise BGM + SFX for the neon intro, locked to the animation's cue times.

Everything is generated from oscillators and noise; no samples.
Usage: python3 synth.py cues.json out.wav
"""
import json
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
DUR = 13.5
N = int(SR * DUR)
rng = np.random.default_rng(7)

cues = json.load(open(sys.argv[1]))
TYPE_END = cues["end"]

# ---------------------------------------------------------------- buses
music = np.zeros((2, N))
sfx = np.zeros((2, N))
rev_send = np.zeros((2, N))
hits = np.zeros((2, N))  # impacts: never ducked by the pre-hit dip


def place(bus, t0, sig, gain=1.0, pan=0.0, rev=0.0):
    """Add a mono or stereo signal at time t0 (s) with equal-power pan."""
    if sig.ndim == 1:
        a = (pan + 1) * np.pi / 4
        sig = np.vstack([sig * np.cos(a), sig * np.sin(a)]) * np.sqrt(2)
    i0 = int(round(t0 * SR))
    if i0 < 0:
        sig = sig[:, -i0:]
        i0 = 0
    n = min(sig.shape[1], N - i0)
    if n <= 0:
        return
    bus[:, i0:i0 + n] += sig[:, :n] * gain
    if rev:
        rev_send[:, i0:i0 + n] += sig[:, :n] * gain * rev


def tt(d):
    return np.arange(int(d * SR)) / SR


def filt(x, kind, f, order=2):
    if kind == "bp":
        sos = butter(order, [f[0] / (SR / 2), f[1] / (SR / 2)], "band", output="sos")
    else:
        sos = butter(order, f / (SR / 2), kind, output="sos")
    return sosfilt(sos, x)


def sweep_filter(x, kind, f_start, f_end, block=512):
    """Filter with an exponentially moving cutoff (bp uses a 1-octave band)."""
    out = np.zeros_like(x)
    nb = int(np.ceil(len(x) / block))
    zi = None
    for k in range(nb):
        f = f_start * (f_end / f_start) ** (k / max(nb - 1, 1))
        if kind == "bp":
            sos = butter(2, [f / 1.41 / (SR / 2), min(f * 1.41, SR / 2 - 100) / (SR / 2)], "band", output="sos")
        else:
            sos = butter(2, min(f, SR / 2 - 100) / (SR / 2), kind, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        seg = x[k * block:(k + 1) * block]
        out[k * block:k * block + len(seg)], zi = sosfilt(sos, seg, zi=zi)
    return out


def noise(d):
    return rng.standard_normal(int(d * SR))


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


def saw(f, d, detune=0.0, maxf=9000):
    t = tt(d)
    ph = rng.random() * 2 * np.pi
    out = np.zeros_like(t)
    f = f * 2 ** (detune / 1200)
    for k in range(1, int(maxf / f) + 1):
        out += np.sin(2 * np.pi * k * f * t + ph * k) / k
    return out * 0.6


def env_adsr(d, a, r, curve=1.0):
    t = tt(d)
    e = np.minimum(1, t / max(a, 1e-4))
    rel = np.clip((d - t) / max(r, 1e-4), 0, 1)
    return (e * rel) ** curve


# ---------------------------------------------------------------- instruments
def kick(amp=1.0, dur=0.5, low=44, high=150):
    t = tt(dur)
    f = low + (high - low) * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 7)
    click = filt(noise(dur), "hp", 2500) * np.exp(-t * 300) * 0.35
    return np.tanh((body + click) * 1.6) * amp


def boom(dur=2.4):
    t = tt(dur)
    f = 30 + 26 * np.exp(-t * 4)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    rumble = filt(noise(dur), "lp", 220) * np.exp(-t * 2.2) * 0.9
    return np.tanh((sub + rumble) * 1.4)


def crash(dur=2.2, amp=1.0):
    t = tt(dur)
    n = np.vstack([filt(noise(dur), "hp", 4200), filt(noise(dur), "hp", 4200)])
    return n * np.exp(-t * 2.3) * 0.5 * amp


def snare(amp=1.0):
    d = 0.3
    t = tt(d)
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 35)
    nz = filt(noise(d), "bp", (1400, 7500)) * np.exp(-t * 17)
    return (tone * 0.6 + nz) * amp


def hat(amp=1.0, open_=False):
    d = 0.25 if open_ else 0.06
    t = tt(d)
    return filt(noise(d), "hp", 8000) * np.exp(-t * (12 if open_ else 70)) * amp


def pluck(m, dur=0.5, bright=1.0):
    f = midi(m)
    t = tt(dur)
    out = np.zeros_like(t)
    for k in range(1, 14):
        if k * f > 12000:
            break
        out += np.sin(2 * np.pi * k * f * t) / k * np.exp(-t * (6 + k * 3.2 / bright))
    return out * np.minimum(1, t / 0.003) * 0.5


def bass(m, dur):
    s = saw(midi(m), dur, maxf=3000) + saw(midi(m), dur, detune=-8, maxf=3000)
    s = filt(s, "lp", 480)
    return s * env_adsr(dur, 0.005, 0.05) * 0.8


def pad(notes, dur, cutoff=1500, attack=0.6, release=0.9):
    L = np.zeros(int(dur * SR))
    R = np.zeros_like(L)
    for m in notes:
        for det, side in ((-11, 0), (0, None), (11, 1)):
            s = saw(midi(m), dur, detune=det, maxf=6000)
            if side in (0, None):
                L += s
            if side in (1, None):
                R += s
    e = env_adsr(dur, attack, release)
    L = filt(L, "lp", cutoff) * e
    R = filt(R, "lp", cutoff) * e
    return np.vstack([L, R]) / (len(notes) * 2)


def riser(dur, f0=300, f1=7000, amp=1.0):
    t = tt(dur)
    nz = sweep_filter(noise(dur), "bp", f0, f1) * 1.8
    f = 110 * (4 ** (t / dur))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    return (nz + tone) * (t / dur) ** 2.2 * amp


def reverse_swell(dur, amp=1.0):
    c = crash(dur, 1.0)[:, ::-1]
    return c * amp


def glitch(dur, amp=1.0, seed=0):
    r = np.random.default_rng(seed)
    out = np.zeros(int(dur * SR))
    i = 0
    while i < len(out):
        g = int(SR * r.uniform(0.012, 0.035))
        kind = r.integers(0, 4)
        t = np.arange(g) / SR
        if kind == 0:
            s = np.sign(np.sin(2 * np.pi * r.uniform(180, 2400) * t))
        elif kind == 1:
            s = r.standard_normal(g)
            hold = r.integers(4, 40)
            s = np.repeat(s[::hold], hold)[:g]
        elif kind == 2:
            s = np.sin(2 * np.pi * r.uniform(60, 400) * t) * 1.5
        else:
            s = np.zeros(g)
        s = np.round(s * 4) / 4  # bit crush
        out[i:i + g] = s[:len(out) - i]
        i += g
    fade = np.minimum(1, np.arange(len(out))[::-1] / (0.01 * SR))
    return np.tanh(out * 0.8) * amp * fade


def beep(f, dur=0.07, amp=1.0):
    t = tt(dur)
    s = np.sin(2 * np.pi * f * t) + 0.2 * np.sign(np.sin(2 * np.pi * f * t))
    return s * np.exp(-t * 30) * np.minimum(1, t / 0.002) * amp


def scan_sweep(dur):
    t = tt(dur)
    nz = sweep_filter(noise(dur), "bp", 900, 5000) * 0.9
    tone = np.sin(2 * np.pi * np.cumsum(500 + 900 * t / dur) / SR) * 0.15
    return (nz + tone) * np.sin(np.pi * t / dur) ** 1.5


def tick(amp=1.0):
    t = tt(0.03)
    return np.sin(2 * np.pi * 3600 * t) * np.exp(-t * 180) * amp


def crt_off():
    d = 0.9
    t = tt(d)
    f = 60 + 2600 * np.exp(-t * 11)
    zap = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    static = filt(noise(d), "hp", 3000) * np.exp(-t * 14) * 0.5
    thunk = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 9) * 0.9
    return (zap * 0.55 + static + thunk)


def key_click(amp=1.0, heavy=False):
    d = 0.06
    t = tt(d)
    c = rng.uniform(2200, 4200)
    nz = filt(noise(d), "bp", (c * 0.7, c * 1.4)) * np.exp(-t * (140 if not heavy else 90))
    thock = np.sin(2 * np.pi * (170 if not heavy else 120) * t) * np.exp(-t * 70) * (0.5 if not heavy else 0.9)
    return (nz * 0.9 + thock) * amp


def send_sound():
    d = 0.6
    t = tt(d)
    pop = np.sin(2 * np.pi * np.cumsum(620 + 500 * np.minimum(1, t / 0.05)) / SR) * np.exp(-t * 22)
    whoosh = sweep_filter(noise(d), "bp", 500, 6000) * np.sin(np.pi * np.minimum(1, t / d)) ** 2 * 0.7
    return pop + whoosh


def bell(m, dur=3.5, amp=1.0):
    f = midi(m)
    t = tt(dur)
    out = np.zeros_like(t)
    for ratio, a, dec in ((1, 1, 1.6), (2.76, .5, 2.8), (5.4, .28, 4.5), (8.93, .15, 7)):
        out += np.sin(2 * np.pi * f * ratio * t) * a * np.exp(-t * dec)
    return out * np.minimum(1, t / 0.002) * amp * 0.5


# ---------------------------------------------------------------- arrangement
BEAT = 0.5
GRID0 = 0.40  # beat grid anchored so the climax (6.38) lands on a downbeat
kick_times = []

# intro riser into the opening flash
place(sfx, 0.0, riser(0.38, 400, 9000, 0.7), rev=0.2)
place(sfx, 0.0, reverse_swell(0.38, 0.9))
# opening impact
place(hits, 0.42, kick(1.2), 1.0)
place(hits, 0.42, boom(2.6), 0.9)
place(hits, 0.42, crash(1.1, 0.6), rev=0.3)
place(sfx, 0.42, glitch(0.25, 0.35, seed=1), pan=-0.3)
kick_times.append(0.42)

# chord plan (D minor): Dm, Bb, C, then the climax back on Dm
chords = [(0.40, 2.40, [50, 57, 62, 65]), (2.40, 4.40, [46, 53, 62, 65]), (4.40, 6.40, [48, 55, 60, 64])]
for a, z, notes in chords:
    cut = 1100 if a < 2 else 1400 if a < 4 else 2200
    place(music, a, pad(notes, z - a + 0.9, cutoff=cut, attack=0.5), 0.8 if a < 2 else 0.55, rev=0.35)

roots = {0: 38, 1: 34, 2: 36}
arp_notes = {0: [62, 65, 69, 74], 1: [62, 65, 70, 74], 2: [60, 64, 67, 72]}

for i in range(int((6.40 - GRID0) / BEAT * 4)):  # 16th grid
    t = GRID0 + i * BEAT / 4
    beat, sub = divmod(i, 4)
    sec = 0 if t < 2.4 else 1 if t < 4.4 else 2
    in_gap = 4.76 <= t < 4.92
    if in_gap:
        continue
    # heartbeat kick in the intro, four-on-the-floor once the HUD starts
    if sub == 0 and (t >= 2.9 or beat % 2 == 0) and t > 0.5:
        place(music, t, kick(0.8 if t < 2.9 else 0.95), 1.0)
        kick_times.append(t)
    # hats from the HUD section
    if t >= 2.9 and sub == 2:
        place(music, t, hat(0.45, open_=beat % 2 == 1), pan=0.25)
    if t >= 4.9 and sub in (1, 3):
        place(music, t, hat(0.22), pan=-0.2)
    # bass on 8ths, off-beat pump
    if t >= 2.9 and sub in (0, 2):
        place(music, t, bass(roots[sec] + (12 if sub == 2 else 0), BEAT / 2 * 0.9), 0.6)
    # plucked arp
    if t >= 2.9:
        n = arp_notes[sec][i % 4] + (12 if (i // 4) % 2 and t >= 4.9 else 0)
        place(music, t, pluck(n, 0.4, bright=1.4 if t >= 4.9 else 0.8), 0.22, pan=(-.35 if i % 2 else .35), rev=0.25)
    # snare on 2 and 4 in the last section, then a roll into the climax
    if t >= 4.9 and sub == 0 and beat % 2 == 1:
        place(music, t, snare(0.8), rev=0.2)

roll_t = 5.90
k = 0
while roll_t < 6.38:
    place(music, roll_t, snare(0.25 + 0.6 * (roll_t - 5.9) / 0.48), rev=0.15)
    roll_t += max(0.03, 0.125 * (1 - (roll_t - 5.9) / 0.6))
    k += 1

# HUD beeps + scan
for i, t in enumerate([2.92, 3.0, 3.08, 3.36]):
    place(sfx, t, beep(2200 if i < 3 else 3300, amp=0.35), pan=-0.4 + i * 0.25)
place(sfx, 3.15, scan_sweep(0.85), 0.5, pan=-0.2, rev=0.2)
# REC blink blips (every 16 frames) while the HUD is up
for f in range(int(3.35 * 30), int(4.75 * 30)):
    if f % 16 == 0:
        place(sfx, f / 30, beep(4400, 0.03, 0.08), pan=-0.6)

# glitch accents
for a, z, s, *_ in cues["glitch"]:
    if a < 0.5:
        continue
    d = max(z - a, 0.06) + 0.04
    place(sfx, a, glitch(d, 0.28 + 0.3 * s, seed=int(a * 100)), pan=0.2)
place(sfx, 4.78, kick(0.8, low=60, high=200), 0.7)

# tagline characters: tiny glassy ticks
for i in range(cues["tagLen"]):
    place(sfx, 5.35 + i * 0.065, tick(0.12), pan=0.3 + 0.02 * i)

# climax
place(sfx, 5.3, riser(1.02, 250, 10000, 0.8), rev=0.3)
place(sfx, 5.6, reverse_swell(0.72, 1.0))
place(hits, 6.38, kick(1.5), 1.2)
place(hits, 6.38, boom(3.0), 1.2)
place(hits, 6.38, crash(2.6, 1.1), rev=0.6)
place(music, 6.40, pad([50, 57, 62, 65, 69], 1.3, cutoff=3200, attack=0.01, release=0.9), 0.8, rev=0.6)
kick_times.append(6.38)

# CRT switch-off
place(sfx, 7.05, crt_off(), 0.8, rev=0.25)

# prompt scene: soft pad, keyboard, send
place(music, 7.85, pad([46, 53, 57, 62], TYPE_END + 1.3 - 7.85, cutoff=1100, attack=0.8, release=0.6), 0.6, rev=0.4)
for s in cues["typing"]:
    if "ch" in s:
        place(sfx, s["t"], key_click(0.45), pan=rng.uniform(-0.15, 0.15))
    else:
        place(sfx, s["t"], key_click(0.55, heavy=True), pan=0.1)
place(sfx, TYPE_END + 0.7, send_sound(), 0.55, rev=0.3)

# end card
t0 = TYPE_END + 1.3
place(sfx, t0, kick(0.7, dur=0.8, low=36, high=90), 0.8)
place(sfx, t0, boom(2.0), 0.4)
for m, dt, p in ((62, 0, -0.2), (69, 0.09, 0.25), (74, 0.18, 0.0)):
    place(sfx, t0 + dt, bell(m, 2.6), 0.35, pan=p, rev=0.6)
place(music, t0, pad([50, 57, 62, 64, 69], DUR - t0, cutoff=2000, attack=0.3, release=1.2), 0.5, rev=0.5)
kick_times.append(t0)

# ---------------------------------------------------------------- mix
# sidechain the music under every kick / impact
duck = np.ones(N)
tn = np.arange(N) / SR
for k in kick_times:
    m = tn >= k
    duck[m] -= 0.55 * np.exp(-(tn[m] - k) * 9)
music *= np.clip(duck, 0.3, 1)

# reverb: decaying stereo noise impulse
ir_len = int(2.6 * SR)
ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 6000), filt(rng.standard_normal(ir_len), "lp", 6000)]) * np.exp(-ti * 2.6)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.5

mix = music * 0.65 + sfx * 0.9 + wet
# pull everything down for a beat before each big hit so the impact jumps out
for h in (0.42, 6.38):
    d = np.ones(N)
    m = (tn > h - 0.09) & (tn < h + 0.02)
    d[m] = 0.2
    d = np.convolve(d, np.ones(240) / 240, 'same')
    mix *= d
mix += hits
mix = np.vstack([filt(mix[c], "hp", 28) for c in range(2)])

# final fade (matches the picture) and a gentle limiter
fade = np.clip((DUR - tn) / 0.4, 0, 1)
mix *= fade
mix = np.tanh(mix / np.abs(mix).max() * 1.6)
mix = mix / np.abs(mix).max() * 10 ** (-1 / 20)

wavfile.write(sys.argv[2], SR, (mix.T * 32767).astype(np.int16))
print("peak dBFS", 20 * np.log10(np.abs(mix).max()), "rms dBFS", 20 * np.log10(np.sqrt((mix ** 2).mean())))
