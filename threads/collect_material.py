#!/usr/bin/env python3
"""Threads 投稿文のネタを集めて表示する（Claude の定期実行から使う）

  python3 threads/collect_material.py [--hours 30]

表示するもの:
  1. 全ブランチの、直近 N 時間のコミット（作業記録）と変更ファイル
  2. 最新の note 有料記事リサーチレポートのパスと、Claude による分析（第7節）
  3. 最近の Threads 投稿（ネタかぶり防止用）

事前に `git fetch origin --prune` しておくこと。
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
NOTE_BRANCH = "origin/claude/note-paid-articles-analysis-0vsrnj"
BOT_MARK = "github-actions[bot]"


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), "-c", "core.quotepath=false", *args], capture_output=True, text=True).stdout


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def work_log(hours: int) -> None:
    section(f"1. 直近{hours}時間の作業記録（全ブランチ）")
    seen = set()
    branches = [b.strip() for b in git("branch", "-r", "--format=%(refname:short)").splitlines()]
    found = False
    for br in branches:
        if br.endswith("/HEAD") or br == "origin":
            continue
        log = git("log", br, f"--since={hours} hours ago", "--format=%H%x09%an%x09%ci%x09%s")
        lines = []
        for row in log.splitlines():
            sha, author, date, subject = row.split("\t", 3)
            # 自動投稿の記録コミット（"Threads:" で始まる）は作業記録に含めない
            if sha in seen or author == BOT_MARK or subject.startswith("Threads:"):
                continue
            seen.add(sha)
            files = git("show", "--stat=120", "--format=", sha).strip().splitlines()
            lines.append(f"- {date[:16]} {subject}")
            lines += [f"    {f.strip()}" for f in files[:8]]
        if lines:
            found = True
            print(f"\n## {br.removeprefix('origin/')}")
            print("\n".join(lines))
    if not found:
        print("（直近のコミットはありません）")


def note_report() -> None:
    section("2. 最新の note 有料記事リサーチ")
    names = git("ls-tree", "--name-only", f"{NOTE_BRANCH}:reports").split()
    reports = sorted(n for n in names if re.match(r"\d{4}-\d{2}-\d{2}\.md$", n))
    if not reports:
        print("（レポートが見つかりません）")
        return
    latest = reports[-1]
    text = git("show", f"{NOTE_BRANCH}:reports/{latest}")
    print(f"レポート: reports/{latest}（ブランチ {NOTE_BRANCH.removeprefix('origin/')}）")
    m = re.search(r"^## 7\..*", text, re.M)
    body = text[m.start():] if m else text
    print(body[:6000])
    if len(body) > 6000:
        print("\n…（省略。全文は上記ファイル）")


def recent_posts(n: int = 10) -> None:
    section(f"3. 最近の投稿（新しい順 {n}件・ネタかぶり防止）")
    files = []
    for d in ("posted", "queue"):
        p = ROOT / d
        if p.is_dir():
            files += [f for f in p.iterdir() if f.suffix in {".md", ".txt"}]
    files.sort(key=lambda f: f.name, reverse=True)
    if not files:
        print("（まだありません）")
    for f in files[:n]:
        print(f"\n--- {f.parent.name}/{f.name}")
        print(re.sub(r"<!--.*?-->\n?", "", f.read_text(encoding="utf-8")).strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=30)
    args = parser.parse_args()
    work_log(args.hours)
    note_report()
    recent_posts()


if __name__ == "__main__":
    main()
