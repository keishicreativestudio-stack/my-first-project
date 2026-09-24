"""台本(YAML)からシーンを組み立てるテンプレート。

- tips     : 「家を買う前に知っておきたい」豆知識(フック → ポイント → 結論 → 保存/フォロー誘導)
- property : 「この家いくら？」物件クイズ(写真 → スペック → 正解発表 → 詳細はプロフへ)
"""
from __future__ import annotations

from .text import card, number_badge, pill, render_text
from .video import W, Layer, Scene, blueprint_bg, kenburns_bg, load_photo

CARD_EMPH = "#E4572E"  # 白カード内の強調色(黄色は白背景で読めないため)


def _read_sec(*texts: str, base: float = 1.3, cps: float = 7.0, min_sec: float = 2.6) -> float:
    """文字数から表示秒数を決める(日本語は1秒7文字くらいが読みやすい)"""
    n = sum(len(str(t).replace("*", "").replace("\n", "")) for t in texts if t)
    return max(min_sec, base + n / cps)


def _headline(text: str, c: dict, size: int = 100, max_width: int = 940):
    return render_text(text, size, c["text"], c["accent"], outline=c["outline"], max_width=max_width)


def _cta_scene(bg, c: dict, brand: dict, main: str, sub: str | None = None) -> Scene:
    s = Scene(3.4, bg)
    s.layers.append(Layer.centered(_headline(main, c, 96), 780, start=0.0))
    if sub:
        s.layers.append(Layer.centered(render_text(sub, 50, c["text"], c["accent"], outline=c["outline"]), 1000, start=0.5, anim="slide"))
    s.layers.append(Layer.centered(pill("フォローして次も見る", 50, c["card_text"], c["accent"]), 1180, start=0.9))
    s.layers.append(Layer.centered(render_text(brand["handle"], 44, c["text"], c["accent"], outline=c["outline"]), 1300, start=1.1, anim="fade", sfx=None))
    return s


# ======================================================================== tips

def build_tips(sc: dict, brand: dict) -> list[Scene]:
    c = brand["colors"]
    bg = blueprint_bg(c)
    scenes: list[Scene] = []

    # 1) フック(最初の1.5秒が勝負)
    hook = Scene(float(sc.get("hook_sec", 3.0)), bg, enter_sfx=None)
    hook.layers.append(Layer.centered(pill(brand.get("tagline", ""), 44, c["card_text"], c["accent"]), 560, start=0.0))
    hook.layers.append(Layer.centered(_headline(sc["hook"], c, 108), 860, start=0.12))
    if sc.get("sub"):
        hook.layers.append(Layer.centered(render_text(sc["sub"], 54, c["text"], c["accent"], outline=c["outline"]), 1160, start=0.8, anim="slide"))
    scenes.append(hook)

    # 2) ポイント
    points = sc.get("points", [])
    for i, p in enumerate(points, 1):
        title, body = p.get("title", ""), p.get("body", "")
        s = Scene(float(p.get("sec") or _read_sec(title, body)), bg)
        badge = number_badge(i, 150, c["card_text"], c["accent"])
        s.layers.append(Layer.centered(badge, 560, start=0.0))
        s.layers.append(Layer.centered(_headline(title, c, 100), 760, start=0.12, anim="slide", sfx=None))
        if body:
            inner = render_text(body, 64, c["card_text"], CARD_EMPH, outline=None, max_width=880, line_gap=1.4)
            cd = card(inner, c["card"])
            s.layers.append(Layer(cd, (W - cd.width) // 2, 880, start=0.55, anim="slide"))
        scenes.append(s)

    # 3) 結論
    if sc.get("conclusion"):
        s = Scene(float(sc.get("conclusion_sec") or _read_sec(sc["conclusion"], base=1.6)), bg)
        s.layers.append(Layer.centered(pill("結論", 60, c["card_text"], c["accent"]), 700, start=0.0))
        s.layers.append(Layer.centered(_headline(sc["conclusion"], c, 110), 950, start=0.2))
        scenes.append(s)

    # 4) 保存・フォロー誘導
    scenes.append(_cta_scene(bg, c, brand, sc.get("cta", "*保存*して\n買う前に見返してね"), sc.get("cta_sub")))
    return scenes


# ======================================================================== property

def build_property(sc: dict, brand: dict) -> list[Scene]:
    c = brand["colors"]
    bp = blueprint_bg(c)
    photos = sc.get("photos") or [{"caption": "外観"}]
    imgs = [load_photo(p.get("file"), p.get("caption", f"写真{i+1}"), i) for i, p in enumerate(photos)]
    scenes: list[Scene] = []

    # 1) フック: この家いくら？
    d = 3.0
    s = Scene(d, kenburns_bg(imgs[0], d, 0), enter_sfx=None)
    s.layers.append(Layer.centered(_headline(sc.get("hook", "この家、\n*いくら*だと思う？"), c, 110), 520, start=0.0))
    if sc.get("area"):
        s.layers.append(Layer.centered(pill(sc["area"], 48, c["card_text"], c["accent"]), 1180, start=0.6, anim="slide"))
    scenes.append(s)

    # 2) 写真を順番に
    for i, (p, im) in enumerate(zip(photos, imgs)):
        if i == 0 and not p.get("caption"):
            continue
        d = float(p.get("sec", 2.6))
        s = Scene(d, kenburns_bg(im, d, i + 1))
        cap = p.get("caption", "")
        if cap:
            inner = render_text(cap, 60, c["card_text"], CARD_EMPH, outline=None, max_width=820)
            cd = card(inner, c["card"], pad=36)
            s.layers.append(Layer(cd, (W - cd.width) // 2, 1150, start=0.15, anim="slide"))
        scenes.append(s)

    # 3) スペック
    specs = sc.get("specs") or {}
    if specs:
        rows = "\n".join(f"{k}　*{v}*" for k, v in specs.items())
        inner = render_text(rows, 64, c["card_text"], CARD_EMPH, outline=None, max_width=860, align="left", line_gap=1.55)
        cd = card(inner, c["card"])
        s = Scene(float(sc.get("specs_sec") or _read_sec(rows, base=1.5, cps=9)), bp)
        s.layers.append(Layer.centered(pill("物件データ", 60, c["card_text"], c["accent"]), 520, start=0.0))
        s.layers.append(Layer(cd, (W - cd.width) // 2, 640, start=0.25, anim="slide"))
        s.layers.append(Layer.centered(render_text("さて、価格は…？", 64, c["text"], c["accent"], outline=c["outline"]),
                                       640 + cd.height + 110, start=1.2, anim="fade"))
        scenes.append(s)

    # 4) 溜め → 正解発表
    s = Scene(1.6, bp)
    s.layers.append(Layer.centered(_headline("正解は…", c, 120), 880, start=0.0))
    s.sfx += [(0.3, "tick"), (0.7, "tick"), (1.1, "tick")]
    scenes.append(s)

    d = 3.2
    s = Scene(d, kenburns_bg(imgs[0], d, 3, dim=0.45), enter_sfx=None)
    price = render_text(f"*{sc['price']}*", 150, c["text"], c["accent"], outline=c["outline"], max_width=1000)
    s.layers.append(Layer.centered(price, 820, start=0.0, anim="stamp", sfx="ding", dur=0.22))
    if sc.get("price_note"):
        s.layers.append(Layer.centered(render_text(sc["price_note"], 46, c["text"], c["accent"], outline=c["outline"]), 980, start=0.5, anim="fade", sfx=None))
    s.layers.append(Layer.centered(render_text(sc.get("comment_prompt", "予想は当たった？\n*コメント*で教えてね"), 62, c["text"], c["accent"], outline=c["outline"]),
                                   1180, start=1.0, anim="slide"))
    scenes.append(s)

    # 5) 詳細はプロフへ + 広告の必要表示
    cta = _cta_scene(bp, c, brand, sc.get("cta", "詳しい情報・内見は\n*プロフィール*の\nリンクから"))
    cta.duration = 4.0
    footer = "\n".join(x for x in [
        f"取引態様：{sc.get('deal_type', '仲介')}",
        brand.get("company", ""),
        brand.get("license", ""),
        sc.get("footer", ""),
    ] if x)
    ft = render_text(footer, 30, c["text"], c["text"], outline=c["outline"], max_width=960, weight_px=0, outline_px=3)
    cta.layers.append(Layer.centered(ft, 1420 + ft.height // 2, start=0.0, anim="none", sfx=None))
    scenes.append(cta)
    return scenes


TEMPLATES = {"tips": build_tips, "property": build_property}
