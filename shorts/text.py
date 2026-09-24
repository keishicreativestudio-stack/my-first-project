"""日本語テキストを画像(RGBA)にするための関数群。

- `*ここ*` で囲んだ部分はアクセントカラーで強調
- 改行は YAML 側で `\n` を書くのが一番きれい。無ければ自動で折り返す(禁則処理つき)
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    # プロジェクト内に置いたフォントを最優先
    "fonts/NotoSansJP-Black.ttf",
    "fonts/NotoSansJP-Bold.ttf",
    # macOS
    "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    # Windows
    "C:/Windows/Fonts/YuGothB.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
]

# 行頭に来てはいけない文字(禁則)
NO_LINE_START = set("、。，．,.・ー―…‥」』）)］]｝}〉》！？!?％%ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ")

_font_path: str | None = None


def set_font(path: str | None) -> str:
    global _font_path
    candidates = ([path] if path else []) + FONT_CANDIDATES
    for c in candidates:
        if c and os.path.exists(c):
            _font_path = c
            return c
    raise FileNotFoundError(
        "日本語フォントが見つかりません。brand.yaml の font にフォントファイルのパスを指定してください。"
    )


@lru_cache(maxsize=64)
def font(size: int) -> ImageFont.FreeTypeFont:
    if _font_path is None:
        set_font(None)
    return ImageFont.truetype(_font_path, size)


def parse_emphasis(text: str) -> list[tuple[str, bool]]:
    """'普通*強調*普通' -> [(char, is_emph), ...]"""
    out: list[tuple[str, bool]] = []
    emph = False
    for ch in text:
        if ch == "*":
            emph = not emph
            continue
        out.append((ch, emph))
    return out


_TOKEN = re.compile(r"[A-Za-z0-9,.%＋+\-/:]+|.", re.S)


def _tokens(chars: list[tuple[str, bool]]) -> list[list[tuple[str, bool]]]:
    """英数字のかたまりは途中で折り返さないように1トークンにまとめる。"""
    s = "".join(c for c, _ in chars)
    toks, i = [], 0
    for m in _TOKEN.finditer(s):
        n = len(m.group(0))
        toks.append(chars[i : i + n])
        i += n
    return toks


def wrap(text: str, size: int, max_width: int) -> list[list[tuple[str, bool]]]:
    f = font(size)
    lines: list[list[tuple[str, bool]]] = []
    for para in str(text).split("\n"):
        chars = parse_emphasis(para)
        line: list[tuple[str, bool]] = []
        for tok in _tokens(chars):
            cand = line + tok
            w = f.getlength("".join(c for c, _ in cand))
            if line and w > max_width and tok[0][0] not in NO_LINE_START:
                lines.append(line)
                line = list(tok)
            else:
                line = cand
        lines.append(line)
    return lines


def render_text(
    text: str,
    size: int,
    color: str,
    accent: str,
    outline: str | None = None,
    max_width: int = 920,
    align: str = "center",
    line_gap: float = 1.28,
    outline_px: int | None = None,
    weight_px: int | None = None,
) -> Image.Image:
    """テキストを透過PNG相当の画像にして返す。"""
    f = font(size)
    lines = wrap(text, size, max_width)
    outline_px = outline_px if outline_px is not None else (max(3, size // 10) if outline else 0)
    weight_px = weight_px if weight_px is not None else max(1, size // 40)  # 疑似太字
    pad = outline_px + weight_px + 4
    line_h = int(size * line_gap)
    widths = [f.getlength("".join(c for c, _ in ln)) for ln in lines]
    W = int(max(widths + [1])) + pad * 2
    H = line_h * len(lines) + pad * 2 + int(size * 0.2)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    for li, (ln, lw) in enumerate(zip(lines, widths)):
        if align == "center":
            x = pad + (W - pad * 2 - lw) / 2
        elif align == "right":
            x = W - pad - lw
        else:
            x = pad
        y = pad + li * line_h
        # 1) フチ
        if outline:
            cx = x
            for ch, _ in ln:
                d.text((cx, y), ch, font=f, fill=outline, stroke_width=outline_px + weight_px, stroke_fill=outline)
                cx += f.getlength(ch)
        # 2) 本体(同色ストロークで太らせる)
        cx = x
        for ch, em in ln:
            col = accent if em else color
            d.text((cx, y), ch, font=f, fill=col, stroke_width=weight_px, stroke_fill=col)
            cx += f.getlength(ch)
    return img


def pill(text: str, size: int, fg: str, bg: str, pad_x: int = 28, pad_y: int = 14) -> Image.Image:
    """角丸の帯(ラベル)"""
    t = render_text(text, size, fg, fg, outline=None, max_width=2000, weight_px=max(1, size // 30))
    W, H = t.width + pad_x * 2, t.height + pad_y * 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, W - 1, H - 1), radius=H // 2, fill=bg)
    img.alpha_composite(t, (pad_x, pad_y))
    return img


def card(content: Image.Image, bg: str, pad: int = 48, radius: int = 36, shadow: bool = True) -> Image.Image:
    """角丸カードの上に content を載せる"""
    W, H = content.width + pad * 2, content.height + pad * 2
    off = 12 if shadow else 0
    img = Image.new("RGBA", (W + off, H + off), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if shadow:
        d.rounded_rectangle((off, off, W - 1 + off, H - 1 + off), radius=radius, fill=(0, 0, 0, 90))
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=radius, fill=bg)
    img.alpha_composite(content, (pad, pad))
    return img


def number_badge(n: int | str, size: int, fg: str, bg: str) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, size - 1, size - 1), fill=bg)
    t = render_text(str(n), int(size * 0.58), fg, fg, outline=None, max_width=size * 2)
    img.alpha_composite(t, ((size - t.width) // 2, (size - t.height) // 2 + 2))
    return img
