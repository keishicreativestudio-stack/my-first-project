"""シーン(背景+レイヤー+効果音)を並べて 1080x1920 の縦動画に書き出すエンジン。"""
from __future__ import annotations

import math
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Callable

from PIL import Image, ImageDraw, ImageFilter

from . import audio

W, H = 1080, 1920
FPS = 30


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def hex2rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


# ---------------------------------------------------------------- easing

def ease_out(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_back(x: float) -> float:
    """少し行き過ぎて戻る(ポップ感)"""
    x = min(max(x, 0.0), 1.0)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


# ---------------------------------------------------------------- layers/scenes

@dataclass
class Layer:
    img: Image.Image
    x: int  # 左上
    y: int
    start: float = 0.0  # シーン内での登場時刻
    anim: str = "pop"  # pop / slide / fade / stamp / none
    sfx: str | None = "pop"
    dur: float = 0.3

    @classmethod
    def centered(cls, img: Image.Image, cy: int, **kw) -> "Layer":
        return cls(img, (W - img.width) // 2, cy - img.height // 2, **kw)


Background = Callable[[float], Image.Image]


@dataclass
class Scene:
    duration: float
    bg: Background
    layers: list[Layer] = field(default_factory=list)
    sfx: list[tuple[float, str]] = field(default_factory=list)  # (シーン内時刻, 名前)
    enter_sfx: str | None = "whoosh"


def _with_alpha(img: Image.Image, a: float) -> Image.Image:
    if a >= 0.999:
        return img
    r, g, b, al = img.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))


def draw_layer(frame: Image.Image, L: Layer, t: float) -> None:
    lt = t - L.start
    if lt < 0:
        return
    p = lt / L.dur if L.dur > 0 else 1.0
    img, x, y = L.img, L.x, L.y
    if L.anim == "none" or p >= 1:
        frame.paste(img, (x, y), img)
        return
    if L.anim in ("pop", "stamp"):
        if L.anim == "pop":
            s = 0.55 + 0.45 * ease_back(p)
        else:
            s = 1.0 + 0.8 * (1 - ease_out(p))
        a = min(1.0, p * 3)
        w, h = max(1, int(img.width * s)), max(1, int(img.height * s))
        im = _with_alpha(img.resize((w, h), Image.BILINEAR), a)
        frame.paste(im, (x + (img.width - w) // 2, y + (img.height - h) // 2), im)
    elif L.anim == "slide":
        dy = int(70 * (1 - ease_out(p)))
        im = _with_alpha(img, ease_out(p))
        frame.paste(im, (x, y + dy), im)
    elif L.anim == "fade":
        im = _with_alpha(img, ease_out(p))
        frame.paste(im, (x, y), im)


# ---------------------------------------------------------------- backgrounds

def blueprint_bg(colors: dict) -> Background:
    """ネイビーのグラデ+方眼(間取り図モチーフ)がゆっくり流れる背景"""
    step = 72
    top, bot, grid = hex2rgb(colors["bg_top"]), hex2rgb(colors["bg_bottom"]), hex2rgb(colors["grid"])
    base = Image.new("RGB", (W, H + step))
    d = ImageDraw.Draw(base)
    for yy in range(H + step):
        k = yy / (H + step)
        d.line([(0, yy), (W, yy)], fill=tuple(int(top[i] * (1 - k) + bot[i] * k) for i in range(3)))
    for xx in range(0, W + 1, step):
        d.line([(xx, 0), (xx, H + step)], fill=grid, width=2 if (xx // step) % 4 == 0 else 1)
    for yy in range(0, H + step + 1, step):
        d.line([(0, yy), (W, yy)], fill=grid, width=2 if (yy // step) % 4 == 0 else 1)

    def f(t: float) -> Image.Image:
        off = int(t * 18) % step
        return base.crop((0, off, W, off + H))

    return f


def placeholder_photo(label: str, seed: int = 0) -> Image.Image:
    """写真が無い時の仮画像(家のイラスト)"""
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    skies = [((120, 180, 235), (220, 235, 250)), ((250, 190, 140), (255, 230, 200)), ((140, 200, 220), (235, 245, 245))]
    s0, s1 = skies[seed % len(skies)]
    for yy in range(H):
        k = yy / H
        d.line([(0, yy), (W, yy)], fill=tuple(int(s0[i] * (1 - k) + s1[i] * k) for i in range(3)))
    d.rectangle((0, 1400, W, H), fill=(120, 170, 110))
    # 家
    walls = [(245, 240, 230), (230, 225, 215), (250, 250, 250)][seed % 3]
    roofs = [(90, 70, 60), (60, 70, 90), (140, 60, 50)][seed % 3]
    d.rectangle((190, 850, 890, 1420), fill=walls, outline=(80, 80, 80), width=4)
    d.polygon([(130, 870), (540, 520), (950, 870)], fill=roofs)
    d.rectangle((460, 1140, 620, 1420), fill=(130, 95, 70))
    for wx in (250, 700):
        d.rectangle((wx, 950, wx + 130, 1080), fill=(170, 210, 235), outline=(90, 90, 90), width=4)
        d.rectangle((wx, 1180, wx + 130, 1310), fill=(170, 210, 235), outline=(90, 90, 90), width=4)
    img = img.filter(ImageFilter.GaussianBlur(1.5))
    from .text import render_text

    t = render_text(f"仮画像:{label}\n(ここに物件写真)", 44, "#FFFFFF", "#FFFFFF", outline="#333333", max_width=900)
    img.paste(t, ((W - t.width) // 2, 1500), t)
    return img


def load_photo(path: str | None, label: str, seed: int) -> Image.Image:
    if path and os.path.exists(path):
        im = Image.open(path).convert("RGB")
        # 縦 9:16 にカバー(はみ出しをトリミング)
        s = max(W / im.width, H / im.height)
        im = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
        l, t = (im.width - W) // 2, (im.height - H) // 2
        return im.crop((l, t, l + W, t + H))
    return placeholder_photo(label, seed)


def shade_overlay(top: float = 0.55, bottom: float = 0.65) -> Image.Image:
    """文字を読みやすくする上下の黒グラデーション"""
    ov = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(ov)
    for yy in range(H):
        k = yy / H
        a = max(top * (1 - k / 0.35) if k < 0.35 else 0, bottom * ((k - 0.55) / 0.45) if k > 0.55 else 0)
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, int(255 * a)))
    return ov


_shade_cache: dict = {}


def kenburns_bg(photo: Image.Image, duration: float, direction: int = 0, dim: float = 0.0) -> Background:
    """写真をゆっくりズーム&パンさせる(静止画でも動いて見える)"""
    Z = 1.18
    big = photo.resize((int(W * Z), int(H * Z)), Image.LANCZOS)
    key = "shade"
    if key not in _shade_cache:
        _shade_cache[key] = shade_overlay()
    shade = _shade_cache[key]
    zoom_in = direction % 2 == 0
    pan = [(-1, 0), (1, 0), (0, -1), (0, 1)][direction % 4]

    def f(t: float) -> Image.Image:
        p = ease_out(t / duration) if duration > 0 else 1
        z = 1.0 + 0.12 * (p if zoom_in else 1 - p)  # 1.0〜1.12
        cw, ch = big.width / z, big.height / z
        cx = big.width / 2 + pan[0] * (big.width - cw) / 2 * (p - 0.5)
        cy = big.height / 2 + pan[1] * (big.height - ch) / 2 * (p - 0.5)
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        fr = big.resize((W, H), Image.BILINEAR, box=box)
        fr.paste(shade, (0, 0), shade)
        if dim > 0:
            fr = Image.blend(fr, Image.new("RGB", (W, H), (0, 0, 0)), dim)
        return fr

    return f


# ---------------------------------------------------------------- render

@dataclass
class Overlay:
    """全シーン共通で上に乗せるもの(シリーズ名・進捗バー)"""
    header: Image.Image | None
    accent: str
    header_y: int = 150


def render(scenes: list[Scene], out_path: str, overlay: Overlay, with_bgm: bool = True,
           bgm_file: str | None = None, bgm_volume: float = 0.35) -> str:
    total = sum(s.duration for s in scenes)
    nframes = int(round(total * FPS))

    # --- 効果音タイムライン
    events: list[tuple[float, str]] = []
    t0 = 0.0
    for i, s in enumerate(scenes):
        if s.enter_sfx and i > 0:
            events.append((max(0, t0 - 0.08), s.enter_sfx))
        for L in s.layers:
            if L.sfx:
                events.append((t0 + L.start, L.sfx))
        events += [(t0 + t, n) for t, n in s.sfx]
        t0 += s.duration

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    tmp = tempfile.mkdtemp()
    wav = os.path.join(tmp, "sfx.wav")
    synth_bgm = with_bgm and not bgm_file
    audio.write_wav(wav, audio.build_track(total, events, synth_bgm, bgm_volume))

    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav]
    if with_bgm and bgm_file:
        cmd += ["-stream_loop", "-1", "-i", bgm_file,
                "-filter_complex",
                f"[2:a]volume={bgm_volume},afade=t=out:st={max(0, total - 1):.2f}:d=1[b];[1:a][b]amix=inputs=2:duration=first:normalize=0[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-t", f"{total:.3f}", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    accent = hex2rgb(overlay.accent)
    bounds = []
    acc = 0.0
    for s in scenes:
        bounds.append((acc, s))
        acc += s.duration
    si = 0
    for fi in range(nframes):
        t = fi / FPS
        while si + 1 < len(bounds) and t >= bounds[si + 1][0]:
            si += 1
        st, scene = bounds[si]
        lt = t - st
        frame = scene.bg(lt).copy()
        for L in scene.layers:
            draw_layer(frame, L, lt)
        if overlay.header is not None:
            h = overlay.header
            frame.paste(h, ((W - h.width) // 2, overlay.header_y), h)
        # 進捗バー(最後まで見たくなる)
        d = ImageDraw.Draw(frame)
        d.rectangle((0, 0, W, 12), fill=(0, 0, 0))
        d.rectangle((0, 0, int(W * (t + 1 / FPS) / total), 12), fill=accent)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg の書き出しに失敗しました")
    return out_path
