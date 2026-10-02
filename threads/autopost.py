#!/usr/bin/env python3
"""Threads 自動投稿スクリプト（Threads 公式 API を使用、標準ライブラリのみ）

使い方:
  python3 threads/autopost.py post            # キューから1件投稿する
  python3 threads/autopost.py post --dry-run  # 投稿せずに、次に投稿される内容を表示する
  python3 threads/autopost.py check           # キューの中身と文字数をチェックする
  python3 threads/autopost.py refresh         # 長期アクセストークンを更新し、新しいトークンを標準出力に出す

キューのルール（threads/queue/ 内の .md / .txt ファイル）:
  - 1ファイル = 1投稿。ファイルの中身がそのまま投稿本文になる。
  - ファイル名が「YYYY-MM-DD_HHMM」で始まる場合、その日時（日本時間）を過ぎてから投稿する。
  - それ以外のファイルは、ファイル名順に「次の空き枠」で投稿する。
  - 1回の実行で投稿するのは1件だけ。
  - 「_」または「.」で始まるファイルは無視する（下書き置き場に使える）。
  - 投稿後は threads/posted/ に移動し、投稿日時と投稿IDを先頭に記録する。

環境変数:
  THREADS_ACCESS_TOKEN  長期アクセストークン（必須。dry-run / check では不要）
  THREADS_USER_ID       Threads ユーザーID（省略時は API から取得）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API_BASE = "https://graph.threads.net/v1.0"
REFRESH_URL = "https://graph.threads.net/refresh_access_token"
MAX_CHARS = 500
JST = timezone(timedelta(hours=9))

ROOT = Path(__file__).resolve().parent
QUEUE_DIR = ROOT / "queue"
POSTED_DIR = ROOT / "posted"

SCHEDULE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})_(\d{2})(\d{2})")


class ThreadsError(RuntimeError):
    pass


def api_request(method: str, url: str, params: dict) -> dict:
    data = None
    if method == "GET":
        url = f"{url}?{urllib.parse.urlencode(params)}"
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        # トークンがログに出ないようにする
        token = params.get("access_token")
        if token:
            body = body.replace(token, "***")
        raise ThreadsError(f"HTTP {e.code} {method} {url.split('?')[0]}: {body}") from None


def scheduled_time(path: Path) -> datetime | None:
    m = SCHEDULE_RE.match(path.name)
    if not m:
        return None
    y, mo, d, h, mi = map(int, m.groups())
    try:
        return datetime(y, mo, d, h, mi, tzinfo=JST)
    except ValueError:
        return None


def queue_files() -> list[Path]:
    if not QUEUE_DIR.is_dir():
        return []
    return sorted(
        p
        for p in QUEUE_DIR.iterdir()
        if p.is_file() and p.suffix in {".md", ".txt"} and not p.name.startswith(("_", "."))
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def pick_next(now: datetime) -> Path | None:
    """日時指定があり期限が来たものを優先し、なければ日時指定なしの先頭を返す。"""
    files = queue_files()
    due = [p for p in files if (t := scheduled_time(p)) and t <= now]
    if due:
        return min(due, key=scheduled_time)
    undated = [p for p in files if not SCHEDULE_RE.match(p.name)]
    return undated[0] if undated else None


def validate(path: Path) -> list[str]:
    text = read_text(path)
    problems = []
    if not text:
        problems.append("本文が空です")
    if len(text) > MAX_CHARS:
        problems.append(f"{len(text)}文字あります（上限{MAX_CHARS}文字）")
    if SCHEDULE_RE.match(path.name) and scheduled_time(path) is None:
        problems.append("ファイル名の日時が正しくありません")
    return problems


def get_user_id(token: str) -> str:
    user_id = os.environ.get("THREADS_USER_ID", "").strip()
    if user_id:
        return user_id
    return api_request("GET", f"{API_BASE}/me", {"fields": "id,username", "access_token": token})["id"]


def publish_text(token: str, text: str) -> str:
    user_id = get_user_id(token)
    container = api_request(
        "POST",
        f"{API_BASE}/{user_id}/threads",
        {"media_type": "TEXT", "text": text, "access_token": token},
    )["id"]

    # コンテナの準備完了を待つ（テキストは通常すぐ終わる）
    for _ in range(12):
        status = api_request(
            "GET", f"{API_BASE}/{container}", {"fields": "status,error_message", "access_token": token}
        )
        if status.get("status") == "FINISHED":
            break
        if status.get("status") in {"ERROR", "EXPIRED"}:
            raise ThreadsError(f"コンテナ作成に失敗しました: {status}")
        time.sleep(5)
    else:
        raise ThreadsError("コンテナの準備が60秒以内に終わりませんでした")

    return api_request(
        "POST",
        f"{API_BASE}/{user_id}/threads_publish",
        {"creation_id": container, "access_token": token},
    )["id"]


def archive(path: Path, post_id: str, now: datetime) -> Path:
    POSTED_DIR.mkdir(parents=True, exist_ok=True)
    dest = POSTED_DIR / f"{now:%Y-%m-%d_%H%M}_{SCHEDULE_RE.sub('', path.name).lstrip('_-') or path.name}"
    header = f"<!-- posted_at: {now.isoformat(timespec='minutes')} / threads_post_id: {post_id} -->\n"
    dest.write_text(header + read_text(path) + "\n", encoding="utf-8")
    path.unlink()
    return dest


def cmd_post(args) -> int:
    now = datetime.now(JST)
    path = pick_next(now)
    if path is None:
        print("投稿待ちのファイルはありません。")
        return 0

    problems = validate(path)
    if problems:
        print(f"::error::{path.name}: " + " / ".join(problems))
        return 1

    text = read_text(path)
    print(f"次の投稿: {path.name}（{len(text)}文字）\n----\n{text}\n----")
    if args.dry_run:
        print("dry-run のため投稿していません。")
        return 0

    token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    if not token:
        print("::error::THREADS_ACCESS_TOKEN が設定されていません")
        return 1

    post_id = publish_text(token, text)
    dest = archive(path, post_id, now)
    print(f"投稿しました（ID: {post_id}）。{dest.relative_to(ROOT.parent)} に移動しました。")
    return 0


def cmd_check(args) -> int:
    files = queue_files()
    if not files:
        print("キューは空です。")
        return 0
    now = datetime.now(JST)
    ng = 0
    for p in files:
        t = scheduled_time(p)
        problems = validate(p)
        when = f"{t:%m/%d %H:%M}以降" if t else "次の空き枠"
        mark = "NG" if problems else "OK"
        ng += bool(problems)
        print(f"[{mark}] {p.name}  {len(read_text(p))}文字  {when}" + (f"  → {' / '.join(problems)}" if problems else ""))
    nxt = pick_next(now)
    print(f"\n次に投稿されるもの: {nxt.name if nxt else '（今はなし。日時指定待ち）'}")
    return 1 if ng else 0


def cmd_refresh(args) -> int:
    token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    if not token:
        print("THREADS_ACCESS_TOKEN が設定されていません", file=sys.stderr)
        return 1
    res = api_request("GET", REFRESH_URL, {"grant_type": "th_refresh_token", "access_token": token})
    days = int(res.get("expires_in", 0)) // 86400
    print(f"トークンを更新しました（有効期限: 約{days}日）", file=sys.stderr)
    print(res["access_token"])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Threads 自動投稿")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_post = sub.add_parser("post", help="キューから1件投稿する")
    p_post.add_argument("--dry-run", action="store_true", help="投稿せずに内容だけ表示する")
    p_post.set_defaults(func=cmd_post)
    sub.add_parser("check", help="キューをチェックする").set_defaults(func=cmd_check)
    sub.add_parser("refresh", help="アクセストークンを更新する").set_defaults(func=cmd_refresh)
    args = parser.parse_args()
    try:
        return args.func(args)
    except ThreadsError as e:
        print(f"::error::{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
