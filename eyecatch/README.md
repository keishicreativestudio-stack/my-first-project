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

## 書き出し方

```
python3 fetch_fonts.py   # 初回だけ。fonts/ にGoogle Fontsをダウンロード
node render.js           # 各案を 1280×670 と 1920×1005 のPNGで書き出す
```

Day番号や文言は各 template*.html の本文を書き換えてください。
