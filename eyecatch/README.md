# note 見出し画像テンプレート（AIチャレンジ365）

| 案 | テンプレート | 方向性 |
|---|---|---|
| A | template.html | 余白型・中央の一言＋スタンプ風アイコン |
| B | template_b.html | 左寄せ＋スタンプ一覧 |
| C | template_c.html | ステッカー型 |
| D | template_d.html | 人生論シリーズ風（生成り色の背景＋縦線＋太い黒文字） |
| E | template_e.html | 静かな明朝体（光の差す淡い背景） |
| F | template_f.html | 調査ノート風（方眼紙＋手書き風の文字＋マーカー） |
| G | template_g.html | 大きな数字（黄色一色＋画面いっぱいの「0」） |
| H | template_h.html | 縦書き（白地に明朝体） |
| I | template_i.html | Q&Aカード（「Q.」で問いかけ、「A.」で予告） |
| J | template_j.html | 雑誌の表紙風（白地＋細い枠線＋号数） |
| K | template_k.html | 調査レポート風（見出し＋控えめな棒グラフ） |
| L | template_l.html | チャットの会話風（質問と答えの吹き出し） |
| J-1 | template_j1.html | J案の派生：生成り×紺、「売れる？」に下線 |
| J-2 | template_j2.html | J案の派生：文芸誌風（二重枠・明朝体・深緑） |
| J-3 | template_j3.html | J案の派生：モダン太枠（黒帯の誌名・赤いラベル） |

## 書き出し方

```
python3 fetch_fonts.py   # 初回だけ。fonts/ にGoogle Fontsをダウンロード
node render.js           # 各案を 1280×670 と 1920×1005 のPNGで書き出す
```

Day番号や文言は各 template*.html の本文を書き換えてください。

## 採用デザイン：J-1（生成り×紺）

`series/` がシリーズ用です。回ごとの文言は `series/episodes.json` に追加します。

```json
"11": {
  "kicker": "特集 ／ テーマ名",
  "title": "1行目、\n2行目は[[強調したい部分]]",
  "foot": ["補足1", "補足2"]
}
```

- `title` の改行は `\n`、からし色の下線を引きたい部分は `[[ ]]` で囲む
- 見出しは1行13字くらいまでに収めると、枠の中にきれいに入ります

書き出し（`series/out/` に 1280×670 と 1920×1005 のPNGができます）:

```
python3 fetch_fonts.py      # 初回だけ
node series/make.js 11
```
