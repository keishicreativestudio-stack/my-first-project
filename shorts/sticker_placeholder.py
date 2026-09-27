"""実物のスタンプ画像が届くまでの仮スタンプ(オリジナルキャラ「もちまる」)を作る。

    python -m shorts.sticker_placeholder assets/stickers/sample
"""
from __future__ import annotations

import math
import os
import sys

from PIL import Image, ImageDraw

from .text import render_text, set_font

SS = 4  # 4倍で描いて縮小(なめらかにする)
SW, SH = 370, 320  # LINEスタンプの最大サイズ

STICKERS = [
    # (ファイル名, セリフ, 表情, 文字色)
    ("01_ryokai", "りょ！", "wink", "#FF7A00"),
    ("02_arigato", "ありがと〜", "happy", "#FF4F8B"),
    ("03_otsukare", "おつかれさま", "smile", "#3AA0FF"),
    ("04_gomen", "ごめんね…", "cry", "#7A8CFF"),
    ("05_erai", "えらい！", "sparkle", "#FFB300"),
    ("06_oyasumi", "おやすみ", "sleep", "#6B5BD6"),
    ("07_muri", "むり…", "dead", "#8A8A8A"),
    ("08_suki", "すき", "love", "#FF3D6E"),
]


def _face(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, kind: str) -> None:
    ink = (60, 45, 40)
    lw = int(r * 0.07)
    ex, ey = r * 0.36, cy - r * 0.08
    er = r * 0.09

    def dot(x, y, rr=er):
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=ink)

    def arc_up(x, y, w=er * 2.2):  # ^ の目
        d.arc((x - w, y - w * 0.4, x + w, y + w * 1.4), 200, 340, fill=ink, width=lw)

    def line(x, y, w=er * 1.8):
        d.line((x - w, y, x + w, y), fill=ink, width=lw)

    # ほっぺ
    for sx in (-1, 1):
        cr = r * 0.16
        d.ellipse((cx + sx * r * 0.58 - cr, ey + r * 0.28 - cr * 0.6, cx + sx * r * 0.58 + cr, ey + r * 0.28 + cr * 0.6),
                  fill=(255, 170, 180))
    L, R = cx - ex, cx + ex
    if kind == "wink":
        dot(L, ey); arc_up(R, ey)
    elif kind in ("happy", "sparkle"):
        arc_up(L, ey); arc_up(R, ey)
    elif kind == "smile":
        dot(L, ey); dot(R, ey)
    elif kind == "cry":
        for x in (L, R):
            d.arc((x - er * 2, ey - er * 1.5, x + er * 2, ey + er * 2), 20, 160, fill=ink, width=lw)
            d.ellipse((x - er * 0.8, ey + er * 2, x + er * 0.8, ey + er * 4.5), fill=(120, 190, 255))
    elif kind == "sleep":
        line(L, ey); line(R, ey)
    elif kind == "dead":
        for x in (L, R):
            w = er * 1.4
            d.line((x - w, ey - w, x + w, ey + w), fill=ink, width=lw)
            d.line((x - w, ey + w, x + w, ey - w), fill=ink, width=lw)
    elif kind == "love":
        for x in (L, R):
            hr = er * 1.5
            d.ellipse((x - hr, ey - hr, x, ey), fill=(255, 60, 100))
            d.ellipse((x, ey - hr, x + hr, ey), fill=(255, 60, 100))
            d.polygon([(x - hr, ey - hr * 0.45), (x + hr, ey - hr * 0.45), (x, ey + hr * 1.1)], fill=(255, 60, 100))
    # 口
    my = ey + r * 0.3
    if kind in ("cry", "dead"):
        d.arc((cx - r * 0.12, my, cx + r * 0.12, my + r * 0.2), 200, 340, fill=ink, width=lw)
    elif kind == "sleep":
        d.ellipse((cx - r * 0.05, my, cx + r * 0.05, my + r * 0.1), fill=ink)
    else:
        d.arc((cx - r * 0.13, my - r * 0.1, cx + r * 0.13, my + r * 0.12), 20, 160, fill=ink, width=lw)


def _deco(img: Image.Image, d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, kind: str) -> None:
    if kind == "sparkle":
        for ang, dist, s in ((-60, 1.25, 0.18), (-20, 1.35, 0.12), (220, 1.3, 0.14)):
            x = cx + math.cos(math.radians(ang)) * r * dist
            y = cy + math.sin(math.radians(ang)) * r * dist
            k = r * s
            d.polygon([(x, y - k), (x + k * 0.3, y - k * 0.3), (x + k, y), (x + k * 0.3, y + k * 0.3),
                       (x, y + k), (x - k * 0.3, y + k * 0.3), (x - k, y), (x - k * 0.3, y - k * 0.3)], fill=(255, 200, 0))
    elif kind == "sleep":
        for dx, dy, s in ((0.95, -1.0, 0.34), (1.3, -1.35, 0.24)):
            t = render_text("Z", int(r * s), "#6B5BD6", "#6B5BD6", outline="#FFFFFF")
            img.paste(t, (int(cx + r * dx), int(cy + r * dy)), t)
    elif kind == "love":
        x, y, k = cx + r * 1.0, cy - r * 0.95, r * 0.18
        d.ellipse((x - k, y - k, x, y), fill=(255, 90, 130))
        d.ellipse((x, y - k, x + k, y), fill=(255, 90, 130))
        d.polygon([(x - k, y - k * 0.45), (x + k, y - k * 0.45), (x, y + k * 1.1)], fill=(255, 90, 130))
    elif kind == "wink":
        # 親指グッ
        hx, hy = cx + r * 0.95, cy + r * 0.1
        d.rounded_rectangle((hx - r * 0.18, hy - r * 0.05, hx + r * 0.2, hy + r * 0.32), radius=int(r * 0.1),
                            fill=(255, 255, 255), outline=(60, 45, 40), width=int(r * 0.05))
        d.rounded_rectangle((hx - r * 0.1, hy - r * 0.32, hx + r * 0.06, hy + r * 0.02), radius=int(r * 0.08),
                            fill=(255, 255, 255), outline=(60, 45, 40), width=int(r * 0.05))


def make_sticker(text: str, kind: str, color: str, tilt: float = 0) -> Image.Image:
    big = Image.new("RGBA", (SW * SS, SH * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    cx, cy, r = SW * SS * 0.5, SH * SS * 0.42, SH * SS * 0.3
    ol = int(r * 0.06)
    # からだ(もち)
    d.ellipse((cx - r * 1.12, cy - r * 0.92, cx + r * 1.12, cy + r * 0.95), fill=(255, 255, 255),
              outline=(60, 45, 40), width=ol)
    # 耳
    for sx in (-1, 1):
        ex = cx + sx * r * 0.62
        d.ellipse((ex - r * 0.2, cy - r * 1.12, ex + r * 0.2, cy - r * 0.7), fill=(255, 255, 255),
                  outline=(60, 45, 40), width=ol)
    d.ellipse((cx - r * 1.12 + ol, cy - r * 0.92 + ol, cx + r * 1.12 - ol, cy + r * 0.95 - ol), fill=(255, 255, 255))
    _face(d, cx, cy, r, kind)
    _deco(big, d, cx, cy, r, kind)
    size = int(min(SH * SS * 0.2, SW * SS * 0.86 / max(1, len(text))))
    t = render_text(text, size, color, color, outline="#FFFFFF", max_width=SW * SS,
                    outline_px=int(SS * 7), weight_px=int(SS * 1.5))
    big.paste(t, (int((SW * SS - t.width) / 2), int(SH * SS - t.height + SS * 6)), t)
    if tilt:
        big = big.rotate(tilt, resample=Image.BICUBIC)
    return big.resize((SW, SH), Image.LANCZOS)


def main(out_dir: str = "assets/stickers/sample") -> None:
    set_font(None)
    os.makedirs(out_dir, exist_ok=True)
    for i, (name, text, kind, color) in enumerate(STICKERS):
        make_sticker(text, kind, color, tilt=(-4, 3, -2, 4)[i % 4]).save(os.path.join(out_dir, name + ".png"))
    print(f"{len(STICKERS)}個の仮スタンプを {out_dir} に作成しました")


if __name__ == "__main__":
    main(*sys.argv[1:])
