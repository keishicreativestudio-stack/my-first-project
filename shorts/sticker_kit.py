"""LINEスタンプ広告の「決まった作業」をまとめた道具。

    # 1) 届いたzipを展開して、スタンプ一覧の画像を作る
    python -m shorts.sticker_kit prepare <スタンプ.zip> <英数字の名前>

    # 2) 台本4本(scripts/sticker/<名前>/*.yaml)から、投稿セット一式を作る
    python -m shorts.sticker_kit package <名前> <フォルダ名> --start 2026-11-05

prepare の結果
  assets/stickers/<名前>/01.png …  動画で使うスタンプ(同じ画像は1枚にまとめる)
  assets/stickers/<名前>_extra/     メイン画像・タブ画像など(動画では使わない)
  output/<名前>_sheet.png           番号つきのスタンプ一覧(中身を読むため)

package の結果(<フォルダ名>/ の中)
  1_1105木_トーク型.mp4 …          投稿順・日付つきの動画
  投稿文.md                         TikTok/固定コメント/Instagram/ストーリーズ/YouTube/X/Threads
  予約表.csv                        TikTok・YouTube・Instagram の予約用(Excelで開ける)
  <フォルダ名>_投稿セット.zip       上の全部をまとめたもの
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import os
import shutil
import io
import re
import sys
import unicodedata
import zipfile

import yaml
from PIL import Image, ImageDraw

from . import text
from .__main__ import build_one, load_brand

IMG_EXT = (".png", ".webp", ".gif", ".jpg", ".jpeg")
EXTRA_WORDS = ("メイン", "タブ", "main", "tab")
WEEKDAYS = "月火水木金土日"


# ============================================================ prepare

def _fix_name(info: zipfile.ZipInfo) -> str:
    """Macなどで作ったzipの日本語ファイル名の文字化けを直す"""
    name = info.filename
    if not info.flag_bits & 0x800:
        raw = name.encode("cp437")
        for enc in ("utf-8", "cp932"):
            try:
                name = raw.decode(enc)
                break
            except UnicodeDecodeError:
                pass
    return unicodedata.normalize("NFC", name)  # Macの「ﾀ+゛」のような分解された濁点をまとめる


def prepare(zip_path: str, slug: str) -> None:
    dst = os.path.join("assets", "stickers", slug)
    extra = dst + "_extra"
    if os.path.exists(dst) and os.listdir(dst):
        sys.exit(f"{dst} はすでにあります。別の名前にするか、先に中身を確認してください")
    os.makedirs(dst, exist_ok=True)
    os.makedirs(extra, exist_ok=True)

    seen: list[tuple[Image.Image, str]] = []
    serifs: list[tuple[str, str]] = []
    stickers, extras, dups = [], [], []
    with zipfile.ZipFile(zip_path) as zf:
        for info in sorted(zf.infolist(), key=_fix_name):
            name = _fix_name(info)
            base = os.path.basename(name)
            if info.is_dir() or "__MACOSX" in name or base.startswith(".") or not base.lower().endswith(IMG_EXT):
                continue
            data = zf.read(info)
            if any(w in base for w in EXTRA_WORDS):
                open(os.path.join(extra, base), "wb").write(data)
                extras.append(base)
                continue
            # 同じ見た目の画像(白背景版など)は1枚にまとめる
            thumb = _thumb(data)
            same = next((label for t, label in seen if _diff(t, thumb) < 8), None)
            words = _serif(base)
            if not same and words:
                same = next((label for w, label in serifs if w == words), None)
            if same:
                dups.append((base, same))
                continue
            serifs.append((words, f"{len(stickers) + 1:02d}({base})"))
            no = f"{len(stickers) + 1:02d}"
            open(os.path.join(dst, no + ".png"), "wb").write(_to_png(data))
            seen.append((thumb, f"{no}({base})"))
            stickers.append((no, base))

    os.makedirs("output", exist_ok=True)
    sheet = os.path.join("output", f"{slug}_sheet.png")
    _contact_sheet([os.path.join(dst, n + ".png") for n, _ in stickers], sheet)

    print(f"スタンプ {len(stickers)} 個 → {dst}/")
    for no, base in stickers:
        print(f"  {no}.png  ← {base}")
    if extras:
        print(f"メイン/タブ画像 → {extra}/: {', '.join(extras)}")
    for base, same in dups:
        print(f"  ※ {base} は {same} と同じスタンプ(白背景版など)とみなして除外しました。必要なら手で戻してください")
    print(f"一覧画像 → {sheet}")


def _serif(filename: str) -> str:
    """ファイル名からセリフ部分だけ取り出す(例: 07_大丈夫です_透過背景.png → 大丈夫です)。
    数字だけの名前(01.png など)なら空文字"""
    stem = os.path.splitext(filename)[0]
    stem = re.sub(r"^\d+[_\-\s]*", "", stem)
    return stem.split("_")[0].strip()


def _thumb(data: bytes) -> Image.Image:
    """白い紙の上に置いた状態の小さな白黒画像(背景が透明か白かの違いを無視して比べるため)"""
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    flat = Image.new("RGB", im.size, "white")
    flat.paste(im, (0, 0), im)
    gray = flat.convert("L")
    bbox = gray.point(lambda v: 255 if v < 235 else 0).getbbox()  # 白以外が描かれている範囲
    if bbox:
        gray = gray.crop(bbox)
    return gray.resize((32, 32), Image.BILINEAR)


def _diff(a: Image.Image, b: Image.Image) -> float:
    return sum(abs(x - y) for x, y in zip(a.getdata(), b.getdata())) / (32 * 32)


def _to_png(data: bytes) -> bytes:
    im = Image.open(io.BytesIO(data))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def _contact_sheet(files: list[str], out: str, cell: int = 300, cols: int = 5) -> None:
    text.set_font(None)
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cell * cols, (cell + 40) * max(rows, 1)), (190, 205, 225))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGBA")
        im.thumbnail((cell - 10, cell - 10))
        x, y = (i % cols) * cell, (i // cols) * (cell + 40)
        sheet.paste(im, (x + 5, y + 5), im)
        d.text((x + 8, y + cell + 6), os.path.basename(f), fill="black", font=text.font(24))
    sheet.save(out)


# ============================================================ package

def _frames_sheet(video: str, out: str, n: int = 8) -> None:
    """動画から均等に n 枚取り出して1枚に並べる(改行・重なり・はみ出しの確認用)"""
    import subprocess
    import tempfile
    from .video import ffmpeg_exe
    ff = ffmpeg_exe()
    dur = 0.0
    info = subprocess.run([ff, "-i", video], capture_output=True, text=True).stderr
    for line in info.splitlines():
        if "Duration:" in line:
            h, m, sec = line.split("Duration:")[1].split(",")[0].strip().split(":")
            dur = int(h) * 3600 + int(m) * 60 + float(sec)
    tmp = tempfile.mkdtemp()
    ims = []
    for i in range(n):
        t = dur * (i + 0.6) / n
        f = os.path.join(tmp, f"{i}.png")
        subprocess.run([ff, "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                        "-vf", "scale=240:-1", f], check=False)
        if os.path.exists(f):
            ims.append(Image.open(f))
    if not ims:
        return
    w, h = ims[0].size
    sheet = Image.new("RGB", ((w + 6) * len(ims), h), "black")
    for i, im in enumerate(ims):
        sheet.paste(im, (i * (w + 6), 0))
    sheet.save(out)


def _post_dates(n: int, start: dt.date, days: str) -> list[dt.date]:
    """start 以降で、days(例 "火木土月")の曜日を順番に拾う"""
    want = [WEEKDAYS.index(c) for c in days]
    out, d = [], start
    while len(out) < n:
        if d.weekday() == want[len(out) % len(want)]:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def _x_len(s: str) -> int:
    """Xの文字数(日本語や絵文字は2、英数字は1で数える。上限280)"""
    return sum(1 if ord(c) < 0x1100 else 2 for c in s)


def _block(title: str, body: str) -> str:
    return f"### {title}\n```\n{body.strip()}\n```\n" if body and body.strip() else ""


def package(slug: str, folder: str, start: dt.date, days: str, brand_path: str, render_video: bool) -> None:
    files = sorted(glob.glob(os.path.join("scripts", "sticker", slug, "*.y*ml")))
    if not files:
        sys.exit(f"scripts/sticker/{slug}/ に台本がありません")
    scs = [yaml.safe_load(open(p, encoding="utf-8")) for p in files]
    dates = _post_dates(len(files), start, days)
    brand = load_brand(brand_path)
    text.set_font(brand.get("font") or None)
    os.makedirs(folder, exist_ok=True)
    work = os.path.join("output", slug)
    os.makedirs(work, exist_ok=True)

    md = [f"# {folder} ― 投稿セット", ""]
    first = scs[0]
    md += [f"- スタンプ名: {first.get('title', '').replace(chr(10), '').replace('*', '')}",
           f"- 検索ワード: 「{first.get('search', '')}」", ""]
    md += ["## 投稿スケジュール", "", "| 日 | 動画 | 時間 |", "|---|---|---|"]
    csv_rows, problems = [], []
    videos = []
    for i, (p, sc, day) in enumerate(zip(files, scs, dates), 1):
        post = sc.get("post") or {}
        label = post.get("label") or os.path.splitext(os.path.basename(p))[0]
        tm = str(post.get("time", "21:00"))
        vname = f"{i}_{day:%m%d}{WEEKDAYS[day.weekday()]}_{label}"
        md.append(f"| {day.month}/{day.day}({WEEKDAYS[day.weekday()]}) | {vname} | {tm} |")
        videos.append((p, sc, day, tm, vname))

    md += ["", "- TikTok・YouTube・Instagram は同じ時間に予約(予約表.csv)。X・Threads は手で投稿",
           "- 投稿後に TikTok と YouTube の固定コメント、Instagram のストーリーズは手で行う", ""]

    for p, sc, day, tm, vname in videos:
        if render_video:
            out = build_one(p, brand, work, with_bgm=True)
            shutil.copy(out, os.path.join(folder, vname + ".mp4"))
            _frames_sheet(out, os.path.join(work, vname + "_frames.png"))
        c = sc.get("captions") or {}
        def cap(key):
            v = c.get(key)
            if not v:
                return ""
            if isinstance(v, str):
                return v.strip()
            tags = " ".join("#" + t.lstrip("#") for t in v.get("hashtags", []))
            return f"{(v.get('caption') or '').strip()}\n\n{tags}".strip()
        missing = [k for k in ("tiktok", "tiktok_pin", "instagram", "x", "youtube_title", "youtube_desc") if not c.get(k)]
        if missing:
            problems.append(f"{os.path.basename(p)}: captions に {', '.join(missing)} がありません")
        search = str(sc.get("search", ""))
        for key in ("tiktok", "tiktok_pin", "instagram", "youtube_desc", "x"):
            body = cap(key)
            if body and search and search not in body:
                problems.append(f"{os.path.basename(p)}: {key} に検索ワード「{search}」が入っていません")
            if any(w in body for w in ("1行目で共感させる", "少し長めの説明", "検索ワード」")) and search != "検索ワード":
                problems.append(f"{os.path.basename(p)}: {key} に型の見本の文が残っています")
        xl = _x_len(cap("x"))
        if xl > 280:
            problems.append(f"{os.path.basename(p)}: X の文字数が {xl}/280 でオーバー")
        md += ["---", "", f"# {vname}", ""]
        md += [_block("TikTok", cap("tiktok")), _block("TikTok 固定コメント", cap("tiktok_pin")),
               _block("Instagram(リール)", cap("instagram")), _block("Instagram ストーリーズ", cap("stories")),
               _block("YouTube タイトル", cap("youtube_title")), _block("YouTube 説明欄", cap("youtube_desc")),
               _block("YouTube 固定コメント", cap("youtube_pin")),
               _block(f"X(文字数 {xl}/280)", cap("x")), _block("X 自分へのリプライ", cap("x_reply")),
               _block("Threads 1つ目", cap("threads")), _block("Threads 2つ目", cap("threads_2"))]
        for sns, title, body, pin in (("TikTok", "", cap("tiktok"), cap("tiktok_pin")),
                                      ("YouTube", cap("youtube_title"), cap("youtube_desc"), cap("youtube_pin")),
                                      ("Instagram", "", cap("instagram"), "")):
            csv_rows.append([f"{day:%Y/%m/%d}", WEEKDAYS[day.weekday()], tm, sns, vname + ".mp4", title, body, pin, ""])

    open(os.path.join(folder, "投稿文.md"), "w", encoding="utf-8").write("\n".join(x for x in md if x is not None))
    with open(os.path.join(folder, "予約表.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["日付", "曜日", "時間", "SNS", "動画", "YouTubeタイトル", "投稿文", "固定コメント", "予約済み"])
        w.writerows(csv_rows)

    zpath = os.path.join(folder, f"{folder}_投稿セット.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
        for f in sorted(os.listdir(folder)):
            if not f.endswith(".zip"):
                z.write(os.path.join(folder, f), f)
    print(f"✔ {folder}/ に投稿セットを作りました(動画 {len(videos)} 本)")
    if render_video:
        print(f"  確認用の場面一覧 → {work}/*_frames.png")
    for p in problems:
        print("  ⚠", p)


# ============================================================ CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shorts.sticker_kit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("prepare", help="zipを展開してスタンプ一覧を作る")
    a.add_argument("zip")
    a.add_argument("slug", help="英数字の名前(例: otter)")
    b = sub.add_parser("package", help="台本から動画・投稿文・予約表・zipを作る")
    b.add_argument("slug")
    b.add_argument("folder", help="できあがりのフォルダ名(例: 社会人カワウソ)")
    b.add_argument("--start", default=dt.date.today().isoformat(), help="最初の投稿日を探し始める日 YYYY-MM-DD")
    b.add_argument("--days", default="火木土月", help="投稿する曜日の順番(例: 火木土月)")
    b.add_argument("--brand", default="brand.yaml")
    b.add_argument("--text-only", action="store_true", help="動画は作り直さず投稿文だけ更新")
    ns = ap.parse_args(argv)
    if ns.cmd == "prepare":
        prepare(ns.zip, ns.slug)
    else:
        package(ns.slug, ns.folder, dt.date.fromisoformat(ns.start), ns.days, ns.brand, not ns.text_only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
