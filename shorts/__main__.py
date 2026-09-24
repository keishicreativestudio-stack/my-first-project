"""使い方:

    python -m shorts scripts/tips/001_shohiyo.yaml          # 1本だけ
    python -m shorts scripts/                               # フォルダ内を全部
    python -m shorts scripts/tips/001_shohiyo.yaml --no-bgm # BGMなし(アプリで流行り音源を付ける用)

書き出し先: output/<台本名>.mp4 と output/<台本名>.txt(投稿文+ハッシュタグ)
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
import time

import yaml

from . import text
from .templates import TEMPLATES
from .video import Overlay, render


def load_brand(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def post_text(sc: dict) -> str:
    cap = (sc.get("caption") or "").strip()
    tags = " ".join("#" + t.lstrip("#") for t in sc.get("hashtags", []))
    return f"{cap}\n\n{tags}".strip() + "\n"


def build_one(path: str, brand: dict, out_dir: str, with_bgm: bool) -> str:
    with open(path, encoding="utf-8") as f:
        sc = yaml.safe_load(f)
    kind = sc.get("type", "tips")
    if kind not in TEMPLATES:
        raise ValueError(f"{path}: type は {list(TEMPLATES)} のどれかにしてください")
    c = brand["colors"]
    header_label = brand["series_name"] + (f"  #{sc['episode']}" if sc.get("episode") else "")
    header = text.pill(header_label, 40, c["text"], "#00000088")
    scenes = TEMPLATES[kind](sc, brand)

    name = os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(out_dir, name + ".mp4")
    bgm = brand.get("bgm") or None
    render(scenes, out, Overlay(header, c["accent"]), with_bgm=with_bgm, bgm_file=bgm,
           bgm_volume=float(brand.get("bgm_volume", 0.35)))
    with open(os.path.join(out_dir, name + ".txt"), "w", encoding="utf-8") as f:
        f.write(post_text(sc))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shorts", description="台本YAMLから縦型ショート動画を作る")
    ap.add_argument("targets", nargs="+", help="台本YAML、またはYAMLが入ったフォルダ")
    ap.add_argument("--brand", default="brand.yaml")
    ap.add_argument("--out", default="output")
    ap.add_argument("--no-bgm", action="store_true", help="BGMを入れない(効果音のみ)")
    a = ap.parse_args(argv)

    brand = load_brand(a.brand)
    print("フォント:", text.set_font(brand.get("font") or None))
    files: list[str] = []
    for t in a.targets:
        if os.path.isdir(t):
            files += sorted(glob.glob(os.path.join(t, "**", "*.y*ml"), recursive=True))
        else:
            files.append(t)
    if not files:
        print("台本が見つかりません", file=sys.stderr)
        return 1
    os.makedirs(a.out, exist_ok=True)
    for p in files:
        t0 = time.time()
        out = build_one(p, brand, a.out, not a.no_bgm)
        print(f"✔ {out}  ({time.time() - t0:.1f}秒)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
