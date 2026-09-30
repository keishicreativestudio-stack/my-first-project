"""96 BPM ironic elevator-bossa score for the 社畜カワウソ ad (15 s, 6 bars).

Bright FM electric piano on bossa voicings, nylon-ish plucked bass, rim clave
and brushes for the working day; at 11 PM the band thins out and detunes,
a fluorescent hum creeps in; the end card goes flat-line, then one monitor
beep and a happy final chord. Effects follow the page cues: chat ping,
hanko stamp on each sticker, blinds rattle, 定時 chime, clock tick.
Usage: python3 otter_synth.py ../audio/synth.py cues.json out.wav
"""
import sys
import numpy as np

base_src, cues_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(base_src).read()
src = src[:src.index("# ---------------------------------------------------------------- instruments")]
src = src.replace("DUR = 13.5", "DUR = 15.0")
sys.argv = [base_src, cues_path, out_path]
exec(src)

C = cues
BEAT = 60 / C["bpm"]
BAR = BEAT * 4
T0 = C["t0"]


def ep(m, dur, vel=1.0, detune=0.0):
    f = midi(m) * 2 ** (detune / 1200)
    t = tt(dur + 0.5)
    idx = 1.6 * np.exp(-t * 4) * vel + 0.2
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    s += np.sin(2 * np.pi * f * 14 * t) * np.exp(-t * 30) * 0.12
    return s * np.exp(-t * 1.1) * np.minimum(1, t / 0.004) * np.clip((dur + 0.5 - t) / 0.5, 0, 1) * vel * 0.28


def chord(notes, t0, dur, vel=1.0, detune=0.0, bus=None):
    for i, m in enumerate(notes):
        place(bus if bus is not None else music, t0 + i * 0.008, ep(m, dur, vel, detune * (1 if i % 2 else -1)), pan=-0.3 + i * 0.2, rev=0.25)


def pluck_bass(m, dur, amp=1.0):
    f = midi(m)
    t = tt(dur)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) * np.exp(-t * 8)
    return s * np.exp(-t * 3) * np.minimum(1, t / 0.003) * np.clip((dur - t) / 0.03, 0, 1) * amp * 0.6


def rim(amp=1.0):
    d = 0.08
    t = tt(d)
    return (np.sin(2 * np.pi * 1800 * t) * 0.6 + filt(noise(d), "bp", (2000, 6000))) * np.exp(-t * 70) * amp * 0.3


def brush(amp=1.0, dur=0.16):
    t = tt(dur)
    return filt(noise(dur), "bp", (3000, 9000)) * np.sin(np.pi * t / dur) * amp * 0.12


def soft_kick(amp=1.0):
    d = 0.25
    t = tt(d)
    return np.sin(2 * np.pi * np.cumsum(48 + 40 * np.exp(-t * 30)) / SR) * np.exp(-t * 12) * amp * 0.7


def ping(amp=1.0):
    d = 0.4
    t = tt(d)
    s = np.sin(2 * np.pi * 1318 * t) * np.exp(-t * 12) * (t < 0.08) + np.sin(2 * np.pi * 1760 * t) * np.exp(-(t - 0.08).clip(0) * 9) * (t >= 0.08)
    return s * amp * 0.3


def hanko_thud(amp=1.0):
    d = 0.3
    t = tt(d)
    thump = np.sin(2 * np.pi * np.cumsum(140 + 80 * np.exp(-t * 50)) / SR) * np.exp(-t * 28)
    slap = filt(noise(d), "bp", (400, 2500)) * np.exp(-t * 60) * 0.6
    return (thump + slap) * amp * 0.9


def rattle(dur=0.44, amp=1.0):
    n = int(dur * SR)
    out = np.zeros(n)
    for k in range(22):
        i = int((k / 22) * dur * SR + rng.uniform(0, 0.006) * SR)
        tk = np.arange(int(0.02 * SR)) / SR
        c = filt(rng.standard_normal(len(tk)), "bp", (1500, 5000)) * np.exp(-tk * 250)
        e = min(n, i + len(c)); out[i:e] += c[:e - i]
    return out * amp * 0.35


def chime_note(m, amp=1.0):
    f = midi(m); t = tt(1.6)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t * 3)) * np.exp(-t * 1.8) * amp * 0.3


def tick(amp=1.0):
    t = tt(0.03)
    return filt(noise(0.03), "bp", (2500, 6000)) * np.exp(-t * 300) * amp * 0.5


def hum(dur, amp=1.0):
    t = tt(dur)
    s = sum(np.sin(2 * np.pi * 50 * k * t) / k for k in (1, 2, 3, 5))
    buzz = filt(noise(dur), "bp", (2000, 4000)) * (0.5 + 0.5 * np.sin(2 * np.pi * 100 * t))
    return (s * 0.3 + buzz * 0.2) * np.minimum(1, t / 0.4) * amp * 0.15


def monitor_beep(dur=0.18, amp=1.0, f=1000):
    t = tt(dur)
    return np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.005) * np.clip((dur - t) / 0.01, 0, 1) * amp * 0.3


# harmony: Fmaj7 Em7 A7 Dm9 Gm7 C9 (bossa ii-V feel)
V = {"F": (41, [57, 60, 64, 69]), "Em7": (40, [55, 59, 62, 67]), "A7": (45, [55, 61, 64, 67]), "Dm9": (38, [53, 57, 60, 64]), "Gm7": (43, [53, 58, 62, 65]), "C9": (36, [52, 58, 62, 64])}
PROG = [["F", "F"], ["Em7", "A7"], ["Dm9", "Gm7"], ["C9", "F"], ["Dm9", "C9"], ["F", "F"]]
MEL = [[72, 74, 76, 79], [79, 77, 76, 73], [74, 77, 81, 79], [76, 74, 72, 70], [69, 67, 65, 64], []]
kicks = []
for bar in range(5):
    night = bar == 4
    for half in range(2):
        t0 = bar * BAR + half * BEAT * 2
        root, notes = V[PROG[bar][half]]
        det = 18 if night else 0
        # bossa comp: on 1, the "and" of 2
        chord(notes, t0, BEAT * 0.8, 0.7 if not night else 0.45, det)
        chord(notes, t0 + BEAT * 1.5, BEAT * 0.4, 0.5 if not night else 0.35, det)
        place(music, t0, pluck_bass(root, BEAT * 0.9, 0.9 if not night else 0.6), 1.0)
        place(music, t0 + BEAT * 1.5, pluck_bass(root + 7, BEAT * 0.45, 0.7), 1.0)
        if not night:
            place(music, t0, soft_kick(0.8), 1.0); kicks.append(t0)
    # clave (3-2) and brushes
    if not night:
        for c in (0, 0.75, 1.5, 2.5, 3):
            place(music, bar * BAR + c * BEAT, rim(0.8), pan=0.3)
    for s8 in range(8):
        place(music, bar * BAR + s8 * BEAT / 2, brush(0.8 if s8 % 2 else 0.5), pan=-0.35)
    for i, m in enumerate(MEL[bar]):
        place(music, bar * BAR + i * BEAT + BEAT * 0.5, ep(m + 12, BEAT * 0.6, 0.5 if not night else 0.3, 25 if night else 0), 1.0, pan=0.2, rev=0.3)

# effects
for i in range(4):
    place(sfx, BEAT * i, tick(0.7), pan=0.2)          # the clock before 9:00
place(sfx, BEAT * 2, ping(0.6), pan=0.1)
for tn_ in C["notify"]:
    place(sfx, tn_, ping(1.0), pan=-0.3)
for ts in C["stamp"]:
    place(sfx, ts, hanko_thud(0.9), pan=0.25)
for k, tt_ in enumerate(C["title"]):
    place(sfx, tt_, hanko_thud(1.1 if k == 2 else 0.8), rev=0.15)
for w in C["wipes"]:
    place(sfx, w - 0.22, rattle(0.44, 0.9))
ch = C["chime"]
for k, m in enumerate([76, 72, 74, 67]):
    place(sfx, ch + k * 0.28, chime_note(m, 0.9), pan=-0.2, rev=0.4)
place(sfx, T0["night"], hum(BAR, 0.8))

# end: flat-line, one beat, then the happy chord
e0 = T0["end"]
place(sfx, C["flat"], monitor_beep(C["beep"] - C["flat"] - 0.02, 0.35, 1000))
place(sfx, C["beep"], monitor_beep(0.12, 1.0, 1000), rev=0.2)
place(sfx, C["beep"] + 0.2, monitor_beep(0.12, 0.8, 1000), rev=0.2)
chord([57, 60, 64, 69, 72], C["beep"] + 0.05, 1.8, 0.9)
place(music, C["beep"] + 0.05, pluck_bass(41, 1.6, 1.0), 1.0)
place(sfx, C["beep"] + 0.08, hanko_thud(1.0))
for s8 in range(int((DUR - C["beep"]) / (BEAT / 2))):
    place(music, C["beep"] + s8 * BEAT / 2, brush(0.5), pan=-0.35)
for k, m in enumerate([81, 84, 88]):
    place(sfx, C["cta"] + k * 0.08, chime_note(m, 0.6), rev=0.4)

# mix
tn = np.arange(N) / SR
duck = np.ones(N)
for k in kicks:
    m = tn >= k; duck[m] -= 0.15 * np.exp(-(tn[m] - k) * 10)
music *= np.clip(duck, 0.8, 1)
# silence the band during the flat-line
gate = np.ones(N); gate[(tn > e0 + 0.05) & (tn < C["beep"])] = 0.0
gate = np.convolve(gate, np.ones(1200) / 1200, "same")
music *= gate
ir_len = int(1.6 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 6000), filt(rng.standard_normal(ir_len), "lp", 6000)]) * np.exp(-ti * 3.5)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.4
out = music * 0.75 + sfx * 0.9 + wet
out = np.vstack([filt(out[c], "hp", 40) for c in range(2)])
out *= np.clip((DUR - tn) / 0.3, 0, 1) * np.clip(tn / 0.01, 0, 1)
out = np.tanh(out / np.abs(out).max() * 1.3)
out = out / np.abs(out).max() * 10 ** (-1 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
for a, b_ in [(0, 2.5), (2.5, 5), (5, 10), (10, 12.5), (12.55, 13.4), (13.5, 15)]:
    s_ = out[:, int(a * SR):int(b_ * SR)]; print(a, b_, round(20 * np.log10(np.sqrt((s_ ** 2).mean()) + 1e-9), 1))
