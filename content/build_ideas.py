"""ネタ一覧（ideas.json）から CSV と Markdown を作り直すスクリプト。

使い方: python3 content/build_ideas.py
ideas.json を編集したら、これを実行すると ideas_50.csv / ideas_50.md が更新されます。
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
FORMATS = {
    "A": "AIに作らせてみた（Claude Code）",
    "B": "ChatGPT活用術（画面録画）",
    "C": "ChatGPT vs Claude 比較",
    "D": "フォトモード（プロンプト集）",
    "E": "コメント返信・シリーズ続編",
}


def main():
    data = json.loads((HERE / "ideas.json").read_text(encoding="utf-8"))
    ideas = data["ideas"]

    with open(HERE / "ideas_50.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["No", "投稿日", "週", "型", "タイトル案", "冒頭テロップ(フック)",
                    "中身の流れ", "締め(CTA)", "ハッシュタグ",
                    "再生数", "完了率(%)", "平均視聴秒", "新規フォロー", "メモ"])
        for i in ideas:
            w.writerow([i["no"], i["date"], i["week"], FORMATS[i["format"]], i["title"],
                        i["hook"], " → ".join(i["flow"]), i["cta"], " ".join(i["tags"]),
                        "", "", "", "", ""])

    lines = ["# 1ヶ月・50本ネタ一覧（TikTok / AI活用ジャンル）", "",
             "`ideas.json` が元データです。編集後は `python3 content/build_ideas.py` で CSV とこのファイルを更新できます。", "",
             "| 型 | 内容 |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in FORMATS.items()]
    for week in sorted({i["week"] for i in ideas}):
        wk = [i for i in ideas if i["week"] == week]
        lines += ["", f"## Week {week}（{data['weeks'][str(week)]}）", ""]
        for i in wk:
            lines += [f"### No.{i['no']}　{i['date']}　[{i['format']}] {i['title']}",
                      f"- **冒頭テロップ**：{i['hook']}",
                      f"- **流れ**：{' → '.join(i['flow'])}",
                      f"- **締め**：{i['cta']}",
                      f"- **タグ**：{' '.join(i['tags'])}", ""]
    lines += ["", "## フック（冒頭1秒）の型 30選", "",
              "ネタに合わせて `◯◯` を差し替えて使います。",
              ""]
    lines += [f"{n}. {h}" for n, h in enumerate(data["hook_bank"], 1)]
    (HERE / "ideas_50.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(ideas)}本を書き出しました")


if __name__ == "__main__":
    main()
