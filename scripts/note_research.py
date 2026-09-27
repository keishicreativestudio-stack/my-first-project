#!/usr/bin/env python3
"""note の「売れている有料記事」リサーチ用データ収集スクリプト。

公開API（ログイン不要）だけを使い、有料記事の購入はしない。
- 人気ハッシュタグの popular 順フィードから有料記事の候補を集める
- 記事詳細から「無料パート本文」「有料部分の残り文字数/画像数」「見出し画像」
  「価格」「スキ数」「購入者レビュー数」「ハッシュタグ」「作者のフォロー/フォロワー数」を取得
- 売れ行きの推定スコアと「フォロワーの少なさに対して売れている度」を算出
- 前日スナップショットとの差分（スキの伸び）も記録

出力:
  data/YYYY-MM-DD/articles.json   全有料記事の詳細
  data/YYYY-MM-DD/eyecatch/*.png  上位記事の見出し画像（分析用、git管理外）
  reports/YYYY-MM-DD.md           定量レポート（定性分析は Claude が追記）

使い方: python3 scripts/note_research.py [--pages 3] [--top 30] [--max-followers 1000]
"""

import argparse
import datetime as dt
import html
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JST = dt.timezone(dt.timedelta(hours=9))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
WAIT = 1.0  # note への負荷を抑えるためのリクエスト間隔（秒）

# 有料記事が多く集まるタグ + 売れ筋ジャンルのタグ
HASHTAGS = [
    "読んでほしい有料記事", "有料記事", "有料note", "note収益化", "noteの書き方",
    "副業", "在宅ワーク", "AI", "ChatGPT", "生成AI", "プロンプト",
    "ブログ", "Kindle出版", "SNS運用", "Instagram", "X運用", "マーケティング",
    "ライティング", "コンテンツ販売", "投資", "株式投資", "FX", "仮想通貨",
    "転職", "キャリア", "フリーランス", "起業", "ビジネス",
    "恋愛", "婚活", "占い", "スピリチュアル", "ダイエット", "美容", "メンタル",
    "子育て", "中学受験", "受験", "英語学習", "資格",
    "競馬", "競艇", "エッセイ", "小説", "イラスト", "デザイン", "プログラミング",
]
# 「110部突破」「50部届きました」など、作者が自己申告している販売部数
SALES_RE = re.compile(r"(\d[\d,]*)\s*部\s*(?:突破|達成|売れ|販売|届|購入|到達)")


def get_json(path):
    url = "https://note.com" + path
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            time.sleep(3 * (attempt + 1))
        except Exception:
            time.sleep(3 * (attempt + 1))
        finally:
            time.sleep(WAIT)
    return None


def strip_html(s):
    s = re.sub(r"<br\s*/?>", "\n", s or "")
    s = re.sub(r"</(p|h\d|li|blockquote|pre)>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(s)).strip()


def headings(s):
    return [strip_html(h) for h in re.findall(r"<h[23][^>]*>(.*?)</h[23]>", s or "", re.S)]


def collect_candidates(pages):
    cands = {}
    for tag in HASHTAGS:
        q = urllib.parse.quote(tag)
        for page in range(1, pages + 1):
            d = get_json(f"/api/v3/hashtags/{q}/notes?order=popular&page={page}")
            if not d:
                break
            data = d.get("data") or {}
            for n in data.get("notes", []):
                if (n.get("price") or 0) > 0 and n.get("key"):
                    c = cands.setdefault(n["key"], {"key": n["key"], "found_in": []})
                    c["found_in"].append(tag)
            if data.get("is_last_page"):
                break
        print(f"  #{tag}: 有料候補 累計 {len(cands)}", file=sys.stderr)
    return cands


def fetch_detail(key):
    d = get_json(f"/api/v3/notes/{key}")
    if not d or not d.get("data"):
        return None
    n = d["data"]
    u = n.get("user") or {}
    body_html = n.get("body") or ""
    free_text = strip_html(body_html)
    sales_claims = [int(m.replace(",", "")) for m in SALES_RE.findall((n.get("name") or "") + "\n" + free_text)]
    return {
        "key": key,
        "url": n.get("note_url"),
        "title": n.get("name"),
        "price": n.get("price"),
        "publish_at": n.get("publish_at"),
        "like_count": n.get("like_count") or 0,
        "comment_count": n.get("comment_count") or 0,
        "rater_count": n.get("rater_count") or 0,
        "share_count": n.get("note_share_total_count") or 0,
        "hashtags": [h["hashtag"]["name"] for h in n.get("hashtag_notes") or [] if h.get("hashtag")],
        "magazine_count": len(n.get("belonging_magazine_keys") or []),
        "has_discount": bool(n.get("discount_campaigns")),
        "prior_sale": n.get("prior_sale"),
        "is_limited": n.get("is_limited"),
        "has_membership": bool(n.get("circle_plans")),
        "eyecatch": n.get("eyecatch"),
        "eyecatch_size": [n.get("eyecatch_width"), n.get("eyecatch_height")],
        "free_text": free_text,
        "free_chars": len(free_text),
        "free_headings": headings(body_html),
        "free_image_count": body_html.count("<img") + body_html.count("<figure"),
        "table_of_contents": [i.get("body") for i in n.get("index") or [] if isinstance(i, dict)],
        "paid_chars": n.get("remained_char_num") or 0,
        "paid_images": n.get("remained_image_num") or 0,
        "paid_files": n.get("remained_file_num") or 0,
        "sales_claims": sales_claims,
        "creator": {
            "urlname": u.get("urlname"),
            "nickname": u.get("nickname"),
            "profile": u.get("profile"),
            "followers": u.get("follower_count") or 0,
            "following": u.get("following_count") or 0,
            "note_count": u.get("note_count") or 0,
            "created_at": u.get("created_at"),
        },
    }


def score(a, prev):
    """売れ行きの推定値。購入者しか付けられないレビュー数を最重視する。"""
    days = 1.0
    try:
        pub = dt.datetime.fromisoformat(a["publish_at"])
        days = max((dt.datetime.now(JST) - pub).total_seconds() / 86400, 1.0)
    except Exception:
        pass
    a["days_since_publish"] = round(days, 1)
    a["likes_per_day"] = round(a["like_count"] / days, 2)
    a["like_growth_1d"] = a["like_count"] - prev["like_count"] if prev else None
    claimed = max(a["sales_claims"]) if a["sales_claims"] else 0
    sales = (a["rater_count"] * 10 + a["like_count"] + a["comment_count"] * 2
             + min(claimed, 1000) * 0.3 + (a["like_growth_1d"] or 0) * 2)
    a["sales_score"] = round(sales * math.log10(a["price"] + 10) / 2, 1)
    f = a["creator"]["followers"]
    a["underdog_score"] = round(a["sales_score"] / math.sqrt(f + 50), 2)


def load_prev(today):
    data_dir = ROOT / "data"
    if not data_dir.exists():
        return {}
    days = sorted(p.name for p in data_dir.iterdir() if p.is_dir() and p.name < today)
    if not days:
        return {}
    f = data_dir / days[-1] / "articles.json"
    if not f.exists():
        return {}
    return {a["key"]: a for a in json.loads(f.read_text())["articles"]}


def download(url, dest):
    try:
        req = urllib.request.Request(url.split("?")[0] + "?width=800", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            dest.write_bytes(r.read())
        return True
    except Exception:
        return False


def median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0


def pct(g, pred):
    return f"{round(100 * sum(1 for a in g if pred(a)) / len(g))}%"


def row(a, i):
    c = a["creator"]
    return (f"| {i} | [{a['title'][:40]}]({a['url']}) | ¥{a['price']:,} | {a['like_count']} | "
            f"{a['rater_count']} | {c['followers']:,} / {c['following']:,} | {a['free_chars']:,} → {a['paid_chars']:,} | "
            f"{a['sales_score']} | {a['underdog_score']} |")


def write_report(today, arts, top, max_followers, path):
    by_sales = sorted(arts, key=lambda a: -a["sales_score"])[:top]
    small = [a for a in arts if a["creator"]["followers"] <= max_followers]
    by_underdog = sorted(small, key=lambda a: -a["underdog_score"])[:top]
    head = ("| # | 記事 | 価格 | スキ | 購入者レビュー | フォロワー / フォロー | 無料文字数 → 有料文字数 | 売れ行き推定 | 少フォロワー指数 |\n"
            "|---|---|---|---|---|---|---|---|---|")
    prices = sorted(a["price"] for a in arts)
    med = prices[len(prices) // 2] if prices else 0
    tag_count = {}
    for a in by_underdog:
        for t in a["hashtags"]:
            tag_count[t] = tag_count.get(t, 0) + 1
    top_tags = sorted(tag_count.items(), key=lambda x: -x[1])[:20]
    L = [f"# note 売れている有料記事リサーチ {today}", "",
         f"- 調査した有料記事: **{len(arts)} 本**（{len(HASHTAGS)} ハッシュタグの人気順フィードから収集）",
         f"- 価格の中央値: ¥{med:,}",
         f"- フォロワー {max_followers:,} 人以下の作者の記事: {len(small)} 本", "",
         "> 売れ行き推定 = 購入者レビュー数×10 + スキ + コメント×2 + 本文中の販売実績表記 + 前日比のスキ増加×2 を価格で補正。",
         "> 少フォロワー指数 = 売れ行き推定 ÷ √(フォロワー+50)。フォロワーが少ないのに売れているほど高い。",
         "> 購入数そのものは note が公開していないため、すべて推定値です。", "",
         f"## 1. フォロワーが少なくても売れている有料記事（フォロワー {max_followers:,} 人以下）", "", head]
    L += [row(a, i + 1) for i, a in enumerate(by_underdog)]
    L += ["", "## 2. 売れ行き推定の総合ランキング", "", head]
    L += [row(a, i + 1) for i, a in enumerate(by_sales)]
    weak = [a for a in arts if a["rater_count"] == 0 and a["like_count"] < 10]
    L += ["", "## 2.5 売れている記事と売れていない記事の比較（中央値）", "",
          "| 指標 | 少フォロワー上位 | 全有料記事 | 反応なし記事（レビュー0・スキ10未満） |", "|---|---|---|---|"]
    for label, fn in [
        ("本数", len),
        ("価格", lambda g: f"¥{median([a['price'] for a in g]):,}"),
        ("無料パート文字数", lambda g: f"{median([a['free_chars'] for a in g]):,}"),
        ("有料パート文字数", lambda g: f"{median([a['paid_chars'] for a in g]):,}"),
        ("有料パート画像数", lambda g: median([a["paid_images"] for a in g])),
        ("作者フォロワー数", lambda g: f"{median([a['creator']['followers'] for a in g]):,}"),
        ("作者の総記事数", lambda g: median([a["creator"]["note_count"] for a in g])),
        ("タイトルに「〇部」表記", lambda g: pct(g, lambda a: re.search(r"\d+\s*部", a["title"]))),
        ("タイトルに【】", lambda g: pct(g, lambda a: "【" in a["title"])),
        ("見出し画像あり", lambda g: pct(g, lambda a: a["eyecatch"])),
    ]:
        L.append(f"| {label} | {fn(by_underdog) if by_underdog else '-'} | {fn(arts) if arts else '-'} | {fn(weak) if weak else '-'} |")
    L += ["", "## 3. 少フォロワー上位記事に多いハッシュタグ", "",
          ", ".join(f"{t}（{n}）" for t, n in top_tags) or "なし", "",
          "## 4. 少フォロワー上位記事の詳細", ""]
    for i, a in enumerate(by_underdog[:15]):
        c = a["creator"]
        L += [f"### {i + 1}. {a['title']}", "",
              f"- URL: {a['url']}",
              f"- 作者: {c['nickname']}（@{c['urlname']}）フォロワー {c['followers']:,} / フォロー {c['following']:,} / 記事数 {c['note_count']}",
              f"- 価格 ¥{a['price']:,} / スキ {a['like_count']} / 購入者レビュー {a['rater_count']} / コメント {a['comment_count']} / 公開 {a['publish_at'][:10]}（{a['days_since_publish']}日前）",
              f"- 前日比スキ増加: {a['like_growth_1d'] if a['like_growth_1d'] is not None else '初登場'}",
              f"- 無料パート {a['free_chars']:,} 字（画像 {a['free_image_count']}）→ 有料パート {a['paid_chars']:,} 字 / 画像 {a['paid_images']} / 添付ファイル {a['paid_files']}",
              f"- 本文中の販売実績表記: {a['sales_claims'] or 'なし'}",
              f"- ハッシュタグ: {' '.join(a['hashtags'])}",
              f"- 見出し画像: {a['eyecatch'] or 'なし'}",
              f"- 無料パートの見出し: {' / '.join(a['free_headings']) or 'なし'}", "",
              "<details><summary>無料パート冒頭（600字）</summary>", "",
              "```", a["free_text"][:600], "```", "</details>", ""]
    path.write_text("\n".join(L) + "\n")
    return by_underdog, by_sales


def save_articles(path, today, arts, keep_full):
    """上位記事以外は無料パート本文を冒頭だけにして、リポジトリの肥大化を防ぐ。"""
    full = {a["key"] for a in keep_full}
    slim = [a if a["key"] in full else {**a, "free_text": a["free_text"][:300]} for a in arts]
    path.write_text(json.dumps({"date": today, "count": len(arts), "articles": slim},
                               ensure_ascii=False, separators=(",", ":")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--max-followers", type=int, default=1000)
    ap.add_argument("--report-only", metavar="YYYY-MM-DD", help="収集せず保存済みデータからレポートだけ作り直す")
    args = ap.parse_args()

    if args.report_only:
        arts = json.loads((ROOT / "data" / args.report_only / "articles.json").read_text())["articles"]
        write_report(args.report_only, arts, args.top, args.max_followers, ROOT / "reports" / f"{args.report_only}.md")
        return

    today = dt.datetime.now(JST).strftime("%Y-%m-%d")
    out = ROOT / "data" / today
    out.mkdir(parents=True, exist_ok=True)
    prev = load_prev(today)

    print("候補収集中...", file=sys.stderr)
    cands = collect_candidates(args.pages)
    arts = []
    for i, (key, c) in enumerate(cands.items()):
        a = fetch_detail(key)
        if not a or not a["price"]:
            continue
        a["found_in"] = c["found_in"]
        score(a, prev.get(key))
        arts.append(a)
        if i % 20 == 0:
            print(f"  詳細 {i + 1}/{len(cands)}", file=sys.stderr)

    (ROOT / "reports").mkdir(exist_ok=True)
    report = ROOT / "reports" / f"{today}.md"
    by_underdog, by_sales = write_report(today, arts, args.top, args.max_followers, report)
    save_articles(out / "articles.json", today, arts, by_underdog[:15] + by_sales[:10])

    eye = out / "eyecatch"
    eye.mkdir(exist_ok=True)
    seen = set()
    for rank, a in enumerate(by_underdog[:15] + by_sales[:10]):
        if a["eyecatch"] and a["key"] not in seen:
            seen.add(a["key"])
            download(a["eyecatch"], eye / f"{a['key']}.png")
    print(f"完了: 有料記事 {len(arts)} 本 → {report.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
