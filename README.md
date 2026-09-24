# 家を買う前の30秒 ― ショート動画自動生成

台本(YAML)を書いてコマンドを1回実行すると、TikTok、Instagram リール、YouTube ショート向けの**縦型動画(1080×1920 MP4)と投稿文**ができます。
顔出しも撮影も要りません。

- 企画、ネタ帳、運用ルール: [`docs/企画書.md`](docs/企画書.md)
- サンプル動画: [`samples/`](samples/)

## できる動画は2種類
| 型 | 台本の例 | 内容 |
|---|---|---|
| 豆知識 `type: tips` | `scripts/tips/001_shohiyo.yaml` | フック → ポイント3つ → 結論 → 保存・フォロー誘導 |
| この家いくら？ `type: property` | `scripts/property/p001_sample.yaml` | 物件写真 → 物件データ → 正解発表 → プロフへ誘導(広告の必要表示つき) |

どちらの型にも、進捗バー、文字のポップアニメーション、効果音、BGM(自動生成で著作権フリー)が入ります。

## はじめかた
```bash
pip install -r requirements.txt

# 1本だけ作る
python -m shorts scripts/tips/001_shohiyo.yaml

# フォルダの台本をまとめて作る
python -m shorts scripts/

# BGMなしで作る(アプリ内で流行りの音源を付けるとき)
python -m shorts scripts/ --no-bgm
```
`output/` に `〇〇.mp4`(動画)と `〇〇.txt`(投稿文とハッシュタグ)ができます。

## 新しい動画を作る手順(5分)
1. 既存の台本をコピーして、`scripts/tips/011_xxx.yaml` のような名前で保存します
2. `hook`、`points`、`conclusion`、`caption` を書き換えます
   - `\n` で改行します。1行14文字くらいまでが読みやすいです
   - `*ここ*` のように `*` で囲むと、その部分が強調色になります
3. `python -m shorts scripts/tips/011_xxx.yaml` を実行します

物件動画の場合は、写真を `assets/photos/<物件名>/` に置いて、台本の `photos` にパスを書いてください。
写真が無い場合は、仮の画像で書き出されます。

## 見た目とアカウント情報の変更
`brand.yaml` で、シリーズ名、アカウント名、色、フォント、BGM、会社名、免許番号を設定します。
**物件動画を投稿する前に、`company` と `license` を必ず自社の内容に書き換えてください。**

フォントは、Mac(ヒラギノ)、Windows(游ゴシック/メイリオ)、Linux(IPA/Noto)の標準フォントを自動で探します。
もっと太いフォントにしたいときは、`fonts/` に Noto Sans JP Black などを置いて `brand.yaml` の `font` で指定してください。

## 構成
```
brand.yaml          チャンネル共通の設定
scripts/            台本(YAML)
assets/photos/      物件写真
assets/bgm/         BGMファイル(任意)
shorts/             動画生成エンジン(Python)
docs/企画書.md       企画、ネタ帳、運用ルール
samples/            サンプル動画
```
