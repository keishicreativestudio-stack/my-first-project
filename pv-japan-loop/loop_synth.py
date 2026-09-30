"""Seamless 30 s loop score (120 BPM, 15 bars) for the endless-zoom trailer.

A Shepard-Risset tone rises forever (one octave every 10 s), under a soft
four-on-the-floor pulse, shaker, sub bass and a koto arpeggio on a 5-chord
cycle (3 cycles = 15 bars). Each picture's window opening gets a glass chime
that climbs a pentatonic ladder, and a low swell leads into it.
Continuous layers are rendered long and cross-faded over the loop point;
one-shot events are rendered long and their tails folded back to the start,
so the file loops with no seam.
Usage: python3 loop_synth.py ../audio/synth.py ../wa/wa_synth.py cues.json out.wav
"""
import sys
import numpy as np

base, wa_path, cues_path, out_path = sys.argv[1:5]
src = open(base).read()
src = src[:src.index("# ---------------------------------------------------------------- arrangement")].replace("DUR = 13.5", "DUR = 36.0")
sys.argv = [base, cues_path, out_path]
exec(src)
wa = open(wa_path).read()
exec(wa[wa.index("\n# ---------------------------------------------------------------- instruments"):wa.index("\n# ---------------------------------------------------------------- arrangement")])

C = cues
LOOP = C["end"]; NL = int(LOOP * SR)
BEAT = 60 / C["bpm"]; BAR = BEAT * 4
tn = np.arange(N) / SR

# ---------------- continuous layer: Shepard tone + pad (rendered to 36 s, crossfaded at the loop)
drone = np.zeros((2, N))
for k in range(7):
    x = (k + tn / 10.0) % 7                      # octave position, rises one octave per 10 s
    f = 55 * 2 ** x
    ph = 2 * np.pi * np.cumsum(f) / SR
    amp = np.exp(-((x - 3.5) / 1.3) ** 2)
    s = np.sin(ph) * amp
    drone[0] += s * (1 + 0.1 * np.sin(k)); drone[1] += s * (1 - 0.1 * np.sin(k))
drone *= 0.09
CH = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67], [52, 55, 59, 64]]
ROOT = [45, 41, 48, 43, 40]
pad_bus = np.zeros((2, N))
for bar in range(int(np.ceil(N / SR / BAR))):
    notes = CH[bar % 5]
    p = pad(notes, BAR + 0.6, cutoff=1400, attack=0.4, release=0.5)
    i0 = int(bar * BAR * SR); n = min(p.shape[1], N - i0)
    if n > 0: pad_bus[:, i0:i0 + n] += p[:, :n] * 0.35
cont = drone + pad_bus

# ---------------- events (placed on bars 0..14 only, tails fold back)
kick_times = []
for bar in range(15):
    t0 = bar * BAR
    notes, root = CH[bar % 5], ROOT[bar % 5]
    for beat in range(4):
        tb = t0 + beat * BEAT
        place(music, tb, kick(0.55, dur=0.35, low=46, high=120), 1.0); kick_times.append(tb)
        place(music, tb + BEAT / 2, hat(0.35), pan=0.3)
        for s in (1, 3): place(music, tb + s * BEAT / 4, hat(0.15), pan=-0.3)
        place(music, tb, bass(root, BEAT * 0.45), 0.45)
        place(music, tb + BEAT / 2, bass(root + 12, BEAT * 0.3), 0.3)
    arp = notes + [notes[1] + 12, notes[2] + 12, notes[3] + 12, notes[2] + 12]
    for e in range(8):
        place(music, t0 + e * BEAT / 2, koto(arp[e] + 12, 1.1, 0.3, bright=0.7), pan=(-0.35 if e % 2 else 0.35), rev=0.35)
LADDER = [76, 79, 81, 84, 86]
for i, tp in enumerate(C["portals"]):
    m = LADDER[i % 5]
    place(sfx, tp, bell(m, 2.4, 0.5), pan=-0.3 + (i % 5) * 0.15, rev=0.6)
    place(sfx, tp - 0.25, reverse_swell(0.3, 0.25))
    place(sfx, tp - BEAT * 1.6 + BAR * 0, riser(BEAT * 1.6, 200, 2500, 0.12)) if i else None
for tm in C["messages"]:
    place(sfx, tm, bell(69, 3.0, 0.45), rev=0.6)
    place(sfx, tm, odaiko(0.45), 1.0, rev=0.5)

# ---------------- mix
duck = np.ones(N)
for k in kick_times:
    m = (tn >= k) & (tn < k + BEAT)
    duck[m] = np.minimum(duck[m], 0.6 + 0.4 * np.clip((tn[m] - k) / (BEAT * 0.7), 0, 1))
music *= duck
ir_len = int(2.8 * SR); ti = np.arange(ir_len) / SR
ir = np.vstack([filt(rng.standard_normal(ir_len), "lp", 6000), filt(rng.standard_normal(ir_len), "lp", 6000)]) * np.exp(-ti * 2.2)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(rev_send[c], ir[c])[:N] for c in range(2)]) * 0.45
events = music * 0.8 + sfx * 0.85 + wet
cont = cont * np.clip(duck, 0.75, 1)

# events: fold everything past the loop point back to the start
out = events[:, :NL].copy()
tail = events[:, NL:]; out[:, :tail.shape[1]] += tail
# continuous: equal-power crossfade from the continuation (t+30) into the fresh start over 5 s
XF = int(5 * SR)
w = np.cos(np.linspace(0, np.pi / 2, XF))
c = cont[:, :NL].copy()
c[:, :XF] = cont[:, NL:NL + XF] * w + cont[:, :XF] * np.sqrt(1 - w ** 2)
out += c
out = np.vstack([filt(np.concatenate([out[ch], out[ch]]), "hp", 30)[NL:] for ch in range(2)])  # filter as a loop
out = np.tanh(out / np.abs(out).max() * 1.5)
out = out / np.abs(out).max() * 10 ** (-1 / 20)
wavfile.write(out_path, SR, (out.T * 32767).astype(np.int16))
seam = np.abs(out[:, 0] - out[:, -1]).max()
print("seam jump", round(float(seam), 4), "rms", round(20 * np.log10(np.sqrt((out ** 2).mean())), 1))
