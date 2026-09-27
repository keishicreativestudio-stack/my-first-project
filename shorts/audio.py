"""効果音とBGMをその場で合成する(著作権フリー・外部素材不要)。"""
from __future__ import annotations

import wave

import numpy as np

SR = 44100


def _env(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / max(decay, 1e-4))


def _lowpass(x: np.ndarray, k: int) -> np.ndarray:
    c = np.cumsum(np.concatenate([np.zeros(k), x]))
    return (c[k:] - c[:-k]) / k


def pop() -> np.ndarray:
    """テキストが出る時の「ポンッ」"""
    n = int(SR * 0.09)
    t = np.arange(n) / SR
    freq = 520 + 900 * t / t[-1]
    return 0.5 * np.sin(2 * np.pi * np.cumsum(freq) / SR) * _env(n, 0.003, 0.03)


def whoosh() -> np.ndarray:
    """場面転換の「シュッ」"""
    n = int(SR * 0.28)
    rng = np.random.default_rng(1)
    x = rng.standard_normal(n)
    x = x - _lowpass(x, 12)  # ハイパス気味
    x = _lowpass(x, 3)
    t = np.linspace(0, 1, n)
    return 0.22 * x * np.sin(np.pi * t) ** 2


def ding() -> np.ndarray:
    """正解発表の「チーン」"""
    n = int(SR * 1.1)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 1318.5 * t) + 0.5 * np.sin(2 * np.pi * 1975.5 * t) + 0.25 * np.sin(2 * np.pi * 2637 * t)
    return 0.3 * x * _env(n, 0.002, 0.35)


def tick() -> np.ndarray:
    """カウントダウンの「コッ」"""
    n = int(SR * 0.05)
    t = np.arange(n) / SR
    return 0.35 * np.sin(2 * np.pi * 1800 * t) * _env(n, 0.001, 0.01)


def msg() -> np.ndarray:
    """メッセージ受信の「ピコッ」(オリジナルの2音)"""
    out = []
    for f, L in ((1046.5, 0.07), (1568.0, 0.12)):
        n = int(SR * L)
        t = np.arange(n) / SR
        out.append(0.28 * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * _env(n, 0.002, L / 2.5))
    return np.concatenate(out)


def boing() -> np.ndarray:
    """スタンプが跳ねる「ぽよん」"""
    n = int(SR * 0.32)
    t = np.arange(n) / SR
    freq = 260 + 180 * np.sin(2 * np.pi * 9 * t) * np.exp(-t / 0.12) + 120 * np.exp(-t / 0.05)
    return 0.45 * np.sin(2 * np.pi * np.cumsum(freq) / SR) * _env(n, 0.003, 0.11)


def sparkle() -> np.ndarray:
    """キラキラ(上昇アルペジオ)"""
    notes = [1568.0, 2093.0, 2637.0, 3136.0]
    step = int(SR * 0.055)
    n = step * len(notes) + int(SR * 0.4)
    out = np.zeros(n)
    for i, f in enumerate(notes):
        L = int(SR * 0.4)
        t = np.arange(L) / SR
        out[i * step : i * step + L] += 0.12 * np.sin(2 * np.pi * f * t) * _env(L, 0.002, 0.12)
    return out


SFX = {"pop": pop, "whoosh": whoosh, "ding": ding, "tick": tick, "msg": msg, "boing": boing, "sparkle": sparkle}


def bgm(duration: float, bpm: float = 100) -> np.ndarray:
    """明るめのローファイ風ループ(C - G - Am - F)"""
    n = int(SR * duration)
    out = np.zeros(n)
    beat = 60 / bpm
    chords = [
        [261.63, 329.63, 392.00],
        [246.94, 293.66, 392.00],
        [220.00, 261.63, 329.63],
        [220.00, 261.63, 349.23],
    ]
    bass = [130.81, 98.00, 110.00, 87.31]
    bar = beat * 4
    rng = np.random.default_rng(7)
    b = 0
    while b * bar < duration:
        ci = b % 4
        start = int(b * bar * SR)
        # パッド(やわらかい和音)
        m = int(bar * SR)
        t = np.arange(m) / SR
        pad = sum(np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.003 * t) for f in chords[ci])
        pad *= 0.035 * np.minimum(1, t / 0.3) * np.minimum(1, (bar - t) / 0.2)
        # ベース
        pad += 0.09 * np.sin(2 * np.pi * bass[ci] * t) * np.exp(-((t % (beat * 2)) / 0.6))
        seg = out[start : start + m]
        seg += pad[: len(seg)]
        # アルペジオ(8分)
        for k in range(8):
            s = start + int(k * beat / 2 * SR)
            f = chords[ci][[0, 1, 2, 1][k % 4]] * 2
            L = int(0.25 * SR)
            tt = np.arange(L) / SR
            note = 0.05 * np.sign(np.sin(2 * np.pi * f * tt)) * _env(L, 0.004, 0.08)
            note = _lowpass(note, 6)
            seg2 = out[s : s + L]
            seg2 += note[: len(seg2)]
        # キック・ハット
        for k in range(4):
            s = start + int(k * beat * SR)
            if k in (0, 2):
                L = int(0.25 * SR)
                tt = np.arange(L) / SR
                kick = 0.35 * np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-tt / 0.03)) / SR) * _env(L, 0.001, 0.09)
                seg2 = out[s : s + L]
                seg2 += kick[: len(seg2)]
            hs = s + int(beat / 2 * SR)
            L = int(0.04 * SR)
            hat = rng.standard_normal(L)
            hat = 0.05 * (hat - _lowpass(hat, 4)) * _env(L, 0.001, 0.01)
            seg2 = out[hs : hs + L]
            seg2 += hat[: len(seg2)]
        b += 1
    # フェードイン/アウト
    fade = int(SR * 0.8)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out


def build_track(duration: float, events: list[tuple[float, str]], with_bgm: bool, bgm_volume: float,
                bpm: float = 100) -> np.ndarray:
    n = int(SR * duration) + 1
    track = np.zeros(n)
    if with_bgm:
        b = bgm(duration, bpm)[:n]
        track[: len(b)] += b * bgm_volume * 2.2
    cache: dict[str, np.ndarray] = {}
    for t, name in events:
        if name not in SFX:
            continue
        s = cache.setdefault(name, SFX[name]())
        i = int(t * SR)
        seg = track[i : i + len(s)]
        seg += s[: len(seg)]
    return track


def write_wav(path: str, x: np.ndarray) -> None:
    x = np.clip(x, -1, 1)
    data = (x * 32767).astype("<i2")
    stereo = np.repeat(data[:, None], 2, axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())
