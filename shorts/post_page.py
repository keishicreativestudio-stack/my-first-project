"""投稿文.md から、ブラウザで見やすい 投稿文.html を作る。

    python -m shorts.post_page モフ雲/投稿文.md      # → モフ雲/投稿文.html

- 動画ごとにカードで表示(タップで開閉)
- 各SNSの文章に「コピー」ボタン
- ファイル1つで完結(ネット接続なしで開ける)
"""
from __future__ import annotations

import html
import os
import re
import sys

VIDEO = re.compile(r"^# (\d+_.*)$", re.M)
SNS_COLOR = {"TikTok": "#FF2D6F", "Instagram": "#B04CE0", "YouTube": "#E53935", "X": "#444", "Threads": "#333"}


def _inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def _md(block: str) -> str:
    """見出し・箇条書き・表・太字くらいだけの簡単な変換"""
    out, table, ul = [], [], False
    def flush_table():
        nonlocal table
        if table:
            rows = [r for r in table if not re.match(r"^\|[\s\-|:]+\|$", r)]
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            h = "".join(f"<th>{_inline(c)}</th>" for c in cells[0])
            b = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in cells[1:])
            out.append(f"<table><tr>{h}</tr>{b}</table>")
            table = []
    for line in block.splitlines():
        if line.startswith("|"):
            table.append(line)
            continue
        flush_table()
        if line.startswith("- "):
            if not ul:
                out.append("<ul>")
                ul = True
            out.append(f"<li>{_inline(line[2:])}</li>")
            continue
        if ul:
            out.append("</ul>")
            ul = False
        if line.startswith("#"):
            level = min(len(line) - len(line.lstrip("#")) + 1, 4)
            out.append(f"<h{level}>{_inline(line.lstrip('#').strip())}</h{level}>")
        elif line.strip() in ("", "---"):
            continue
        elif line.startswith(">"):
            out.append(f"<p class=note>{_inline(line.lstrip('> '))}</p>")
        else:
            out.append(f"<p>{_inline(line)}</p>")
    flush_table()
    if ul:
        out.append("</ul>")
    return "\n".join(out)


def _body(text: str) -> str:
    """コードブロック(```)はコピーボタン付きの枠、それ以外は普通の文章"""
    parts = re.split(r"```\n?(.*?)```", text, flags=re.S)
    out = []
    for i, p in enumerate(parts):
        if i % 2:
            out.append(f'<div class=copy><button onclick="cp(this)">コピー</button><pre>{html.escape(p.strip())}</pre></div>')
        elif p.strip():
            out.append(_md(p.strip()))
    return "\n".join(out)


def _sns_color(label: str) -> str:
    for k, c in SNS_COLOR.items():
        if label.startswith(k):
            return c
    return "#666"


def build(md_path: str, out_path: str | None = None) -> str:
    md = open(md_path, encoding="utf-8").read()
    title = md.splitlines()[0].lstrip("# ").strip()
    marks = list(VIDEO.finditer(md))
    first = marks[0].start() if marks else len(md)
    pre = md[len(md.splitlines()[0]):first]
    cards, notes = [], ""
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(md)
        sec = md[m.end():end]
        # 動画セクションの後ろに続く別の話題(「# メモ」や「## 返信の例」)はメモに回す
        tail = re.search(r"\n(# (?!\d+_)|## )", sec)
        if tail:
            notes += sec[tail.start():]
            sec = sec[:tail.start()]
        name = m.group(1).strip()
        mm = re.match(r"(\d+)_(\d{2})(\d{2})(.)_(.*)", name)
        head = f"{int(mm.group(2))}/{int(mm.group(3))}({mm.group(4)}) {mm.group(5)}" if mm else name
        blocks = []
        for b in re.split(r"\n(?=### )", sec.strip()):
            if not b.startswith("### "):
                continue
            label, body = (b[4:].split("\n", 1) + [""])[:2]
            blocks.append(f'<section><h3 style="--c:{_sns_color(label)}">{html.escape(label)}</h3>{_body(body)}</section>')
        cards.append(f'<details{" open" if i == 0 else ""}><summary><span class=no>{mm.group(1) if mm else i + 1}</span>'
                     f'{html.escape(head)}<small>{html.escape(name)}.mp4</small></summary>{"".join(blocks)}</details>')

    page = f"""<!doctype html><html lang=ja><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>
:root{{--bg:#f5f6f8;--card:#fff;--text:#1d2330;--sub:#667085;--line:#e3e6eb;--pre:#f7f8fa}}
@media (prefers-color-scheme:dark){{:root{{--bg:#15171c;--card:#1f232b;--text:#e9ecf1;--sub:#9aa3b2;--line:#303641;--pre:#171a20}}}}
body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 -apple-system,"Hiragino Sans","Yu Gothic",sans-serif}}
main{{max-width:760px;margin:auto;padding:16px}}
h1{{font-size:20px;margin:8px 0 12px}} h2,h3,h4{{margin:14px 0 6px}}
.intro,.notes{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:4px 16px 12px;margin-bottom:14px}}
table{{border-collapse:collapse;width:100%;font-size:14px}} th,td{{border-bottom:1px solid var(--line);padding:6px 4px;text-align:left}}
details{{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:12px 0;overflow:hidden}}
summary{{cursor:pointer;padding:14px 16px;font-weight:700;font-size:16px;list-style:none;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
summary::-webkit-details-marker{{display:none}}
summary small{{font-weight:400;color:var(--sub);font-size:12px;width:100%}}
.no{{background:#3C4E74;color:#fff;border-radius:50%;width:26px;height:26px;display:inline-grid;place-items:center;font-size:13px}}
section{{border-top:1px solid var(--line);padding:6px 16px 12px}}
section h3{{font-size:14px;color:var(--c);margin:10px 0 6px}}
.copy{{position:relative;margin:6px 0}}
pre{{background:var(--pre);border:1px solid var(--line);border-radius:8px;padding:38px 12px 12px;margin:0;white-space:pre-wrap;word-break:break-word;font:14px/1.6 inherit;font-family:inherit}}
button{{position:absolute;top:6px;right:6px;border:0;border-radius:6px;padding:4px 10px;background:#3C4E74;color:#fff;font-size:12px;cursor:pointer}}
button.ok{{background:#2E9E5B}}
p{{margin:4px 0}} p.note{{color:var(--sub)}} code{{background:var(--pre);padding:1px 4px;border-radius:4px}}
</style></head><body><main>
<h1>{html.escape(title)}</h1>
<div class=intro>{_md(pre.strip())}</div>
{"".join(cards)}
{f'<div class=notes>{_md(notes.strip())}</div>' if notes.strip() else ''}
</main><script>
function cp(b){{const t=b.nextElementSibling.innerText;
 const done=()=>{{b.textContent='コピーしました';b.classList.add('ok');setTimeout(()=>{{b.textContent='コピー';b.classList.remove('ok')}},1500)}};
 if(navigator.clipboard&&window.isSecureContext){{navigator.clipboard.writeText(t).then(done,()=>fb(t,done))}}else fb(t,done)}}
function fb(t,done){{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();
 try{{document.execCommand('copy');done()}}catch(e){{}}a.remove()}}
</script></body></html>"""
    out_path = out_path or os.path.splitext(md_path)[0] + ".html"
    open(out_path, "w", encoding="utf-8").write(page)
    return out_path


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print("✔", build(p))
