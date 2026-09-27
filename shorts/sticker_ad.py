"""LINEスタンプ広告のテンプレート(type: sticker)

variant:
  chat  : トーク型   … 「あるある」な会話にスタンプで返す場面を3つ見せる(使う場面が想像できる)
  tempo : テンポ型   … 「○○な時に」+スタンプを1秒ずつリズムよく見せる(種類の多さ・便利さ)
  quiz  : クイズ型   … 「今の気分どれ？」で番号をコメントしてもらう(コメント・ループ再生)

どの型も最後は 全種類の一覧 → 購入導線(ショップ検索ワード / プロフのリンク) で締める。

※LINEのガイドライン上、トーク画面を模したデザインは「LINEと異なる色・形」にする必要があるため、
  吹き出しは角丸・しっぽ無し・パステル配色のオリジナルデザインにしています(LINEロゴも使いません)。
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFilter

from .text import number_badge, pill, render_text
from .video import H, W, Layer, Scene, hex2rgb

DEFAULT_THEME = {
    "bg": "#FFF4EC",        # 背景グラデ上
    "bg2": "#FFE1EA",       # 背景グラデ下
    "pattern": "#FFFFFF",   # 背景の水玉
    "text": "#3B2B2B",      # テロップ文字
    "accent": "#FF4F8B",    # *強調* ・ボタン
    "header": "#FF8FB1",    # トーク画面のヘッダー
    "chat_bg": "#FBF8F6",   # トーク画面の中
    "them": "#EFEAE6",      # 相手の吹き出し
    "me": "#FFD6E3",        # 自分の吹き出し
}


# ------------------------------------------------------------------ 素材

class Stickers:
    def __init__(self, sc: dict):
        self.dir = sc.get("stickers_dir", "assets/stickers/sample")
        exts = (".png", ".webp", ".gif", ".jpg", ".jpeg")
        self.files = sorted(f for f in os.listdir(self.dir) if f.lower().endswith(exts)) if os.path.isdir(self.dir) else []
        if not self.files:
            raise FileNotFoundError(f"スタンプ画像が見つかりません: {self.dir}")
        self._cache: dict[str, Image.Image] = {}

    def get(self, name: str | int | None) -> Image.Image:
        if name is None:
            name = self.files[0]
        if isinstance(name, int):
            name = self.files[(name - 1) % len(self.files)]
        if name not in self._cache:
            path = name if os.path.exists(name) else os.path.join(self.dir, name)
            im = Image.open(path).convert("RGBA")
            bbox = im.getbbox()  # 余白を詰める
            self._cache[name] = im.crop(bbox) if bbox else im
        return self._cache[name]

    def sized(self, name, max_w: int, max_h: int | None = None) -> Image.Image:
        im = self.get(name)
        max_h = max_h or max_w
        s = min(max_w / im.width, max_h / im.height)
        return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def _shadow(img: Image.Image, blur: int = 14, alpha: int = 60, off: int = 10) -> Image.Image:
    """スタンプの下にふんわり影を付けて背景から浮かせる"""
    pad = blur * 2 + off
    out = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: min(alpha, v))
    sh = Image.new("RGBA", img.size, (80, 40, 60, 0))
    sh.putalpha(a)
    out.paste(sh, (pad, pad + off), sh)
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(img, (pad, pad))
    return out


def pastel_bg(th: dict, alt: bool = False):
    """パステルのグラデ+水玉がゆっくり流れる背景"""
    top, bot = hex2rgb(th["bg"]), hex2rgb(th["bg2"])
    if alt:
        top, bot = bot, top
    step = 150
    base = Image.new("RGB", (W, H + step))
    d = ImageDraw.Draw(base)
    for yy in range(H + step):
        k = yy / (H + step)
        d.line([(0, yy), (W, yy)], fill=tuple(int(top[i] * (1 - k) + bot[i] * k) for i in range(3)))
    dot = Image.new("RGBA", base.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(dot)
    pr = hex2rgb(th["pattern"])
    for row, yy in enumerate(range(0, H + step * 2, step)):
        for xx in range(-step, W + step, step):
            x = xx + (step // 2 if row % 2 else 0)
            dd.ellipse((x - 14, yy - 14, x + 14, yy + 14), fill=pr + (110,))
    base.paste(dot, (0, 0), dot)

    def f(t: float) -> Image.Image:
        off = int(t * 30) % step
        return base.crop((0, step - off, W, step - off + H))

    return f


def telop(text: str, th: dict, size: int = 92, max_width: int = 960) -> Image.Image:
    return render_text(text, size, th["text"], th["accent"], outline="#FFFFFF", max_width=max_width,
                       outline_px=max(8, size // 7))


# ------------------------------------------------------------------ トーク画面

PANEL = (60, 560, 1020, 1420)  # x0, y0, x1, y1 (SNSのUIに隠れない範囲)
HEADER_H = 104


def chat_panel(th: dict, partner: str, h: int | None = None) -> Image.Image:
    x0, y0, x1, y1 = PANEL
    w, h = x1 - x0, h or (y1 - y0)
    img = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((12, 20, w + 12, h + 20), radius=52, fill=(90, 40, 60, 70))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w, h), radius=52, fill=th["chat_bg"])
    d.rounded_rectangle((0, 0, w, HEADER_H + 52), radius=52, fill=th["header"])
    d.rectangle((0, HEADER_H, w, HEADER_H + 52), fill=th["chat_bg"])
    name = render_text(partner, 44, "#FFFFFF", "#FFFFFF", outline=None, max_width=700)
    img.alpha_composite(name, ((w - name.width) // 2, (HEADER_H - name.height) // 2 + 4))
    cy = HEADER_H // 2  # 戻る矢印(フォントに頼らず描く)
    d.line((58, cy - 20, 38, cy, 58, cy + 20), fill="#FFFFFF", width=8, joint="curve")
    return img


def bubble(text: str, fill: str, fg: str = "#3B2B2B", size: int = 50, max_w: int = 600) -> Image.Image:
    t = render_text(text, size, fg, "#FF4F8B", outline=None, max_width=max_w, line_gap=1.3, weight_px=1)
    px, py = 34, 22
    img = Image.new("RGBA", (t.width + px * 2, t.height + py * 2 - 8), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=40, fill=fill)
    img.alpha_composite(t, (px, py - 4))
    return img


def avatar(partner: str, color: str, size: int = 84) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, size - 1, size - 1), fill=color)
    ch = render_text(partner[:1] or "?", int(size * 0.5), "#FFFFFF", "#FFFFFF", outline=None)
    img.alpha_composite(ch, ((size - ch.width) // 2, (size - ch.height) // 2 + 2))
    return img


def small(text: str, color: str = "#9A8F8A", size: int = 28) -> Image.Image:
    return render_text(text, size, color, color, outline=None, weight_px=0)


def chat_scene(sc_item: dict, th: dict, st: Stickers, bg, caption_size: int = 88) -> Scene:
    x0, y0, x1, y1 = PANEL
    partner = sc_item.get("partner", "ともだち")
    layers: list[Layer] = []

    y = y0 + HEADER_H + 36
    t = 0.3
    av_color = th["header"]
    for m in sc_item.get("messages", []):
        mine = m.get("from", "them") == "me"
        if "sticker" in m:
            im = _shadow(st.sized(m["sticker"], int(m.get("size", 470)), 410), blur=8, alpha=45, off=6)
            x = (x1 - 30 - im.width + 12) if mine else (x0 + 130 - 12)
            layers.append(Layer(im, x, y - 30, start=t, anim="pop", sfx="boing", dur=0.38, idle="wiggle", idle_amp=0.6))
            if mine:
                meta = small("既読\n" + m.get("time", "12:03"))
                layers.append(Layer(meta, x + 10 - meta.width, y + im.height - 60 - meta.height, start=t + 0.1, anim="fade", sfx=None))
            y += im.height - 40
            gap = 0.95
        else:
            b = bubble(m["text"], th["me"] if mine else th["them"])
            if mine:
                x = x1 - 40 - b.width
            else:
                x = x0 + 130
                layers.append(Layer(avatar(partner, av_color), x0 + 30, y - 4, start=t, anim="pop", sfx=None, dur=0.25))
            layers.append(Layer(b, x, y, start=t, anim="slide", sfx="msg" if not mine else "pop", dur=0.25))
            y += b.height + 26
            gap = 0.55 + 0.035 * len(m["text"])
        t += float(m.get("wait", gap))
    # パネルの高さは中身に合わせる(下がスカスカにならないように)
    ph = min(y1 - y0, max(460, y - y0 + 50))
    # 見出し+トーク画面をひとかたまりにして、画面の中央(SNSのUIに隠れない範囲)に置く
    cap = telop(sc_item["caption"], th, caption_size) if sc_item.get("caption") else None
    cap_h = cap.height + 40 if cap else 0
    area_top, area_bottom = 300, 1440
    top = area_top + max(0, (area_bottom - area_top - cap_h - ph) // 2)
    dy = top + cap_h - y0
    for L in layers:
        L.y += dy
    head = [Layer(chat_panel(th, partner, ph), x0 - 12, y0 - 4 + dy, start=0.0, anim="none", sfx=None)]
    if cap:
        head.insert(0, Layer(cap, (W - cap.width) // 2, top, start=0.0, anim="pop", sfx=None))
    layers = head + layers
    return Scene(float(sc_item.get("sec") or (t + 1.0)), bg, layers)


# ------------------------------------------------------------------ 共通シーン

def burst(th: dict, size: int = 1100, rays: int = 16) -> Image.Image:
    """スタンプの後ろで回る放射状の光(集中線)"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    for i in range(rays):
        a0 = 2 * math.pi * i / rays
        a1 = a0 + math.pi / rays
        d.polygon([(c, c), (c + c * 1.5 * math.cos(a0), c + c * 1.5 * math.sin(a0)),
                   (c + c * 1.5 * math.cos(a1), c + c * 1.5 * math.sin(a1))], fill=(255, 255, 255, 120))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(size // 10))
    img.putalpha(Image.composite(img.split()[3], Image.new("L", img.size, 0), mask))
    ImageDraw.Draw(img).ellipse((c - size * 0.26, c - size * 0.26, c + size * 0.26, c + size * 0.26), fill=(255, 255, 255, 150))
    return img


_burst_cache: dict = {}


def burst_layer(th: dict, cy: int, start: float = 0.0, size: int = 1100) -> Layer:
    key = (th["accent"], size)
    if key not in _burst_cache:
        _burst_cache[key] = burst(th, size)
    b = _burst_cache[key]
    return Layer(b, (W - b.width) // 2, cy - b.height // 2, start=start, anim="fade", sfx=None, dur=0.2, idle="spin")


def hook_scene(sc: dict, th: dict, st: Stickers, bg) -> Scene:
    s = Scene(float(sc.get("hook_sec", 1.9)), bg, enter_sfx=None)
    cap = telop(sc["hook"], th, 104)
    s.layers.append(Layer(cap, (W - cap.width) // 2, 470 - cap.height // 2, start=0.0, anim="pop", sfx="pop"))
    s.layers.append(burst_layer(th, 1040, 0.2))
    im = _shadow(st.sized(sc.get("hook_sticker", 1), 640, 560))
    s.layers.append(Layer(im, (W - im.width) // 2, 1040 - im.height // 2, start=0.25, anim="stamp", sfx="boing",
                          dur=0.22, idle="wiggle"))
    return s


def lineup_scene(sc: dict, th: dict, st: Stickers, bg) -> Scene:
    names = sc.get("lineup") or st.files
    n_total = int(sc.get("count") or len(st.files))
    names = names[:16]
    cols = 4 if len(names) > 9 else 3 if len(names) > 4 else 2
    rows = math.ceil(len(names) / cols)
    cell_w = 940 // cols
    cell_h = min(300, 900 // rows)
    top = 600 + (900 - rows * cell_h) // 2 - 60
    s = Scene(float(sc.get("lineup_sec", 3.0)), bg)
    cap = telop(sc.get("lineup_text", f"毎日使える\n*全{n_total}種*"), th, 96)
    s.layers.append(Layer(cap, (W - cap.width) // 2, 400 - cap.height // 2, start=0.0, anim="pop", sfx="sparkle"))
    for i, nm in enumerate(names):
        r, c = divmod(i, cols)
        im = st.sized(nm, cell_w - 24, cell_h - 16)
        x = 70 + c * cell_w + (cell_w - im.width) // 2
        yy = top + r * cell_h + (cell_h - im.height) // 2
        s.layers.append(Layer(im, x, yy, start=0.25 + i * 0.09, anim="pop", sfx="pop" if i % 2 == 0 else None,
                              dur=0.3, idle="bob", idle_amp=0.5))
    return s


def cta_scene(sc: dict, th: dict, st: Stickers, bg) -> Scene:
    s = Scene(float(sc.get("cta_sec", 3.4)), bg)
    title = telop(sc.get("title", ""), th, 80)
    s.layers.append(Layer(title, (W - title.width) // 2, 330 - title.height // 2, start=0.0, anim="pop", sfx=None))
    s.layers.append(burst_layer(th, 760, 0.1, 1000))
    im = _shadow(st.sized(sc.get("main_sticker", 1), 600, 520))
    s.layers.append(Layer(im, (W - im.width) // 2, 760 - im.height // 2, start=0.1, anim="pop", sfx="sparkle",
                          dur=0.35, idle="bob"))
    shop = pill(sc.get("cta", f"LINEスタンプショップで\n「{sc.get('search', '')}」で検索"), 56, "#FFFFFF", th["accent"],
                pad_x=48, pad_y=24)
    # 2行のピルは角丸を小さく
    if shop.height > 150:
        t = render_text(sc.get("cta", f"LINEスタンプショップで\n「{sc.get('search', '')}」で検索"), 56, "#FFFFFF", "#FFE45C",
                        outline=None, weight_px=2)
        shop = Image.new("RGBA", (t.width + 96, t.height + 44), (0, 0, 0, 0))
        ImageDraw.Draw(shop).rounded_rectangle((0, 0, shop.width - 1, shop.height - 1), radius=44, fill=th["accent"])
        shop.alpha_composite(t, (48, 22))
    s.layers.append(Layer(shop, (W - shop.width) // 2, 1140, start=0.45, anim="pop", sfx="pop", idle="pulse"))
    sub = render_text(sc.get("cta_sub", "プロフのリンクからもすぐ買えます"), 46, th["text"], th["accent"], outline="#FFFFFF",
                      outline_px=6)
    s.layers.append(Layer(sub, (W - sub.width) // 2, 1160 + shop.height + 20, start=0.8, anim="fade", sfx=None))
    return s


# ------------------------------------------------------------------ 型ごとの構成

def build_sticker_ad(sc: dict, brand: dict) -> list[Scene]:
    th = {**DEFAULT_THEME, **(sc.get("theme") or {})}
    st = Stickers(sc)
    bg, bg2 = pastel_bg(th), pastel_bg(th, alt=True)
    v = sc.get("variant", "chat")
    scenes: list[Scene] = []

    if v == "chat":
        scenes.append(hook_scene(sc, th, st, bg))
        for i, item in enumerate(sc.get("chats", [])):
            scenes.append(chat_scene(item, th, st, bg2 if i % 2 == 0 else bg))

    elif v == "tempo":
        scenes.append(hook_scene(sc, th, st, bg))
        beat = 60 / float(sc.get("bpm", 120))
        tag = pill(sc["tempo_tag"], 44, "#FFFFFF", th["accent"], pad_x=30, pad_y=12) if sc.get("tempo_tag") else None
        for i, item in enumerate(sc.get("items", [])):
            s = Scene(float(item.get("sec", beat * 2)), bg2 if i % 2 == 0 else bg, enter_sfx=None)
            if "sticker" not in item:
                # 文字だけの場面(「…と見せかけて」などの切り替え)
                cap = telop(item["label"], th, int(item.get("size", 120)))
                s.layers.append(Layer(cap, (W - cap.width) // 2, 900 - cap.height // 2, start=0.0, anim="stamp",
                                      sfx=item.get("sfx", "whoosh"), dur=0.2, idle="pulse"))
                scenes.append(s)
                continue
            if tag is not None:
                s.layers.append(Layer(tag, (W - tag.width) // 2, 300, start=0.0, anim="none", sfx=None))
            cap = telop(item["label"], th, 92)
            s.layers.append(Layer(cap, (W - cap.width) // 2, 470 - cap.height // 2, start=0.0, anim="slide", sfx=None, dur=0.18))
            s.layers.append(burst_layer(th, 1010))
            im = _shadow(st.sized(item["sticker"], 680, 600))
            s.layers.append(Layer(im, (W - im.width) // 2, 1010 - im.height // 2, start=0.06, anim="stamp", sfx="boing",
                                  dur=0.18, idle="wiggle"))
            scenes.append(s)

    elif v == "quiz":
        q = sc.get("quiz", {})
        choices = q.get("choices") or st.files[:4]
        s = Scene(float(q.get("sec", 5.5)), bg, enter_sfx=None)
        cap = telop(sc.get("hook", "今の気分\n*どれ？*"), th, 104)
        s.layers.append(Layer(cap, (W - cap.width) // 2, 420 - cap.height // 2, start=0.0, anim="pop", sfx="pop"))
        cell = 440
        for i, nm in enumerate(choices[:4]):
            r, c = divmod(i, 2)
            im = st.sized(nm, cell - 50, 330)
            cx, cy = 100 + c * cell + cell // 2, 790 + r * 380
            s.layers.append(Layer(im, cx - im.width // 2, cy - im.height // 2, start=0.35 + i * 0.22, anim="pop",
                                  sfx="boing", dur=0.32, idle="bob", idle_amp=0.5))
            b = number_badge(i + 1, 84, "#FFFFFF", th["accent"])
            s.layers.append(Layer(b, cx - im.width // 2 - 58, cy - b.height // 2 + 20, start=0.45 + i * 0.22, anim="pop", sfx=None))
        ask = pill(q.get("ask", "コメントで番号おしえて！"), 52, "#FFFFFF", th["accent"], pad_x=44, pad_y=20)
        s.layers.append(Layer(ask, (W - ask.width) // 2, 1390, start=1.6, anim="pop", sfx="ding", idle="pulse"))
        scenes.append(s)
    else:
        raise ValueError(f"variant は chat / tempo / quiz のどれかにしてください: {v}")

    if sc.get("show_lineup", True):
        scenes.append(lineup_scene(sc, th, st, bg2))
    scenes.append(cta_scene(sc, th, st, bg))
    return scenes
