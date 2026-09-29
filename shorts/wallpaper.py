"""キャラ入りのカレンダー壁紙(スマホの待ち受け用)を作る。

    python -m shorts.wallpaper 2026 11            # docs/wallpapers.yaml の全キャラ分 → 壁紙/2026-11/

- サイズは iPhone の待ち受け(1179×2556)
- 上3分の1は時計やウィジェットのために空けておく
- 日曜・祝日は赤、土曜は青。祝日は docs/wallpapers.yaml の holidays に書く
"""
from __future__ import annotations

import calendar
import os
import sys

import yaml
from PIL import Image, ImageDraw, ImageFilter

from . import text
from .sticker_ad import Stickers, _shadow
from .video import hex2rgb

WW, WH = 1179, 2556
RED, BLUE = "#E0483E", "#3A6FD8"


def _background(th: dict) -> Image.Image:
    top, bot = hex2rgb(th["bg"]), hex2rgb(th["bg2"])
    img = Image.new("RGB", (WW, WH))
    d = ImageDraw.Draw(img)
    for y in range(WH):
        k = y / WH
        d.line([(0, y), (WW, y)], fill=tuple(int(top[i] * (1 - k) + bot[i] * k) for i in range(3)))
    dots = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots)
    step = 130
    for r, y in enumerate(range(0, WH + step, step)):
        for x in range(-step, WW + step, step):
            x2 = x + (step // 2 if r % 2 else 0)
            dd.ellipse((x2 - 12, y - 12, x2 + 12, y + 12), fill=(255, 255, 255, 120))
    img.paste(dots, (0, 0), dots)
    return img


def make(year: int, month: int, ch: dict, holidays: dict[int, str], out: str) -> None:
    th = ch["theme"]
    img = _background(th).convert("RGBA")
    d = ImageDraw.Draw(img)

    # ── 月の見出し(時計の下) ──
    title = text.render_text(f"*{month}*月", 120, th["text"], th["accent"], outline="#FFFFFF", outline_px=10)
    sub = text.render_text(f"{calendar.month_name[month]} {year}", 44, th["text"], th["text"], outline="#FFFFFF",
                           outline_px=6, weight_px=1)
    y0 = 760
    img.alpha_composite(title, ((WW - title.width) // 2, y0))
    img.alpha_composite(sub, ((WW - sub.width) // 2, y0 + title.height - 10))

    # ── カレンダー(半透明の白いカード) ──
    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)  # 日曜はじまり
    cw, rh = 138, 96
    gx = (WW - cw * 7) // 2
    gy = y0 + title.height + sub.height + 30
    card_h = 90 + rh * len(weeks) + 30
    panel = Image.new("RGBA", (cw * 7 + 60, card_h), (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle((0, 0, panel.width - 1, panel.height - 1), radius=44, fill=(255, 255, 255, 190))
    img.alpha_composite(panel, (gx - 30, gy))
    for i, wd in enumerate("日月火水木金土"):
        col = RED if i == 0 else BLUE if i == 6 else th["text"]
        t = text.render_text(wd, 40, col, col, outline=None, weight_px=1)
        img.alpha_composite(t, (gx + i * cw + (cw - t.width) // 2, gy + 24))
    for r, week in enumerate(weeks):
        for c, day in enumerate(week):
            if not day:
                continue
            col = RED if c == 0 or day in holidays else BLUE if c == 6 else th["text"]
            cx, cy = gx + c * cw + cw // 2, gy + 90 + r * rh + rh // 2
            if day in (ch.get("mark") or {}):
                d.ellipse((cx - 46, cy - 46, cx + 46, cy + 46), fill=th["accent"])
                col = "#FFFFFF"
            t = text.render_text(str(day), 52, col, col, outline=None, weight_px=1)
            img.alpha_composite(t, (cx - t.width // 2, cy - t.height // 2 - 4))
            if day in holidays:
                h = text.render_text(holidays[day], 20, RED, RED, outline=None, weight_px=0)
                img.alpha_composite(h, (cx - h.width // 2, cy + 30))
    gy_end = gy + card_h

    # ── キャラと一言 ──
    st = Stickers({"stickers_dir": ch["stickers_dir"]})
    area_top, area_bottom = gy_end + 30, 2330  # 下のほうはライト・カメラのボタンを避ける
    say = text.render_text(ch["say"], 58, th["text"], th["accent"], outline="#FFFFFF", outline_px=8, max_width=1000)
    img.alpha_composite(say, ((WW - say.width) // 2, area_top))
    room = area_bottom - (area_top + say.height + 10)
    im = _shadow(st.sized(ch["sticker"], min(700, room + 60), room + 20))
    img.alpha_composite(im, ((WW - im.width) // 2, area_top + say.height + 10 + (room - im.height) // 2))

    # ── 小さくスタンプ名 ──
    foot = text.render_text(f"LINEスタンプ「{ch['name']}」", 30, th["text"], th["text"], outline="#FFFFFF",
                            outline_px=4, weight_px=0)
    img.alpha_composite(foot, ((WW - foot.width) // 2, 2380))

    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.convert("RGB").save(out, quality=95)


def main(argv: list[str]) -> int:
    year, month = int(argv[0]), int(argv[1])
    conf = yaml.safe_load(open("docs/wallpapers.yaml", encoding="utf-8"))
    text.set_font(None)
    holidays = {int(k): v for k, v in (conf.get("holidays", {}).get(f"{year}-{month:02d}") or {}).items()}
    outs = []
    for ch in conf["characters"]:
        say = (ch.get("say") or {}).get(f"{year}-{month:02d}") or ch.get("say_default", "")
        c = {**ch, "say": say, "mark": {int(k): v for k, v in ((ch.get("mark") or {}).get(f"{year}-{month:02d}") or {}).items()}}
        out = os.path.join("壁紙", f"{year}-{month:02d}", f"{year}-{month:02d}_{ch['name']}.png")
        make(year, month, c, holidays, out)
        outs.append(out)
        print("✔", out)
    # 4枚並べた確認用
    ims = [Image.open(o) for o in outs]
    sheet = Image.new("RGB", (sum(i.width // 3 + 10 for i in ims), WH // 3), "white")
    x = 0
    for i in ims:
        sheet.paste(i.resize((i.width // 3, i.height // 3)), (x, 0))
        x += i.width // 3 + 10
    sheet.save(os.path.join("output", f"wallpapers_{year}-{month:02d}.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
