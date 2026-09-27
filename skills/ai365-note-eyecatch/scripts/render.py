#!/usr/bin/env python3
"""AIチャレンジ365 の見出し画像（J-1デザイン）を書き出す。

使い方:
  python3 render.py variants.json [出力フォルダ]

variants.json の例:
  [
    {"id": "12a", "no": 12, "kicker": "AI副業 ／ 12日目",
     "title": "1行目、\\n2行目は[[強調]]", "foot": ["下の段の文"]}
  ]

- title の改行は \\n、からし色の下線を引く部分は [[ ]] で囲む
- foot は1要素なら1つの文、2要素以上なら「・」で区切って並ぶ
- 出力: <id>.html（常に）と、Playwright が使えれば
  ai365_day<id>_1280x670.png / _1920x1005.png
"""
import glob
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = (HERE.parent / "assets" / "template.html").read_text(encoding="utf-8")


def fill(v):
    title = html.escape(v["title"])
    title = re.sub(r"\[\[(.+?)\]\]", r"<u>\1</u>", title).replace("\n", "<br>")
    foot = "<span>・</span>".join(f"<span>{html.escape(f)}</span>" for f in v["foot"])
    return (TEMPLATE.replace("{{no}}", html.escape(str(v["no"])))
            .replace("{{kicker}}", html.escape(v["kicker"]))
            .replace("{{title}}", title)
            .replace("{{foot}}", foot))


def launch(pw):
    """Playwright 同梱のブラウザ、なければ環境にある Chromium を探して起動する。"""
    try:
        return pw.chromium.launch()
    except Exception:
        pass
    candidates = [os.environ.get("CHROMIUM_PATH", "")]
    candidates += glob.glob("/opt/pw-browsers/chromium*/chrome-linux*/chrome")
    candidates += [shutil.which(n) or "" for n in ("chromium", "chromium-browser", "google-chrome")]
    for exe in filter(None, candidates):
        try:
            return pw.chromium.launch(executable_path=exe)
        except Exception:
            continue
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    variants = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "out")
    out.mkdir(parents=True, exist_ok=True)
    pages = []
    for v in variants:
        p = out / f"{v['id']}.html"
        p.write_text(fill(v), encoding="utf-8")
        pages.append((v["id"], p))
        print("HTML:", p)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright がないためPNGは書き出していません。HTMLをブラウザで 1280×670 で表示してください。")
        return
    with sync_playwright() as pw:
        browser = launch(pw)
        if browser is None:
            print("ブラウザを起動できないためPNGは書き出していません。HTMLをブラウザで 1280×670 で表示してください。")
            return
        for vid, p in pages:
            for scale, size in ((1, "1280x670"), (1.5, "1920x1005")):
                page = browser.new_page(viewport={"width": 1280, "height": 670}, device_scale_factor=scale)
                page.goto(p.resolve().as_uri(), wait_until="networkidle")
                page.evaluate("document.fonts.ready")
                png = out / f"ai365_day{vid}_{size}.png"
                page.screenshot(path=str(png))
                page.close()
                print("PNG:", png)
        browser.close()


if __name__ == "__main__":
    main()
