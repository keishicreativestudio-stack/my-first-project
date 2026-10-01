# CLAUDE.md

TikTok アカウント「AIチャレンジ365」（@aichallenge365）の運用リポジトリ。
AI活用ジャンル、顔出し・声出しなし。台本 JSON から `tiktok-studio/make_video.py` で縦型動画やフォトモード画像を作る。

## 台本を作るときのルール

- 台本は `tiktok-studio/scripts/YYYY-MM-DD.json`、投稿メモは `tiktok-studio/scripts/YYYY-MM-DD_投稿メモ.md` に置く。
- 台本には必ず次を入れる。
  - `handle`: `@aichallenge365`
  - `series`: `AIチャレンジ DayN`（10/1 が Day1）
  - **`caption`（TikTok の説明文）と `hashtags`（ハッシュタグ）を、投稿ごとに内容に合わせて毎回作る。**
- 説明文の書き方:
  - 2〜3行。1行目に動画の結論と、検索されやすい言葉（ChatGPT、献立、仕事効率化など）を入れる。
  - 最後はコメントしたくなる問いかけで終える。
  - 誇張しない。実際に起きたこと（かかった時間など）だけを書く。本人の経歴など、確認していないことは書かない。
  - AI で作った画像を使った回は、その旨を説明文にも書く。
- ハッシュタグ: 5〜6個。大きいタグ（#ChatGPT、#AI活用 など）と内容に合う小さいタグを混ぜ、最後は必ず `#AIチャレンジ365`。
- 動画・画像を書き出すと `out/台本名_caption.txt` に説明文とハッシュタグが出るので、ユーザーにはその中身も渡す。

## ネタと進め方

- 1ヶ月分のネタは `content/ideas_50.md`（元データ `content/ideas.json`）。
- 画面録画などの素材は `tiktok-studio/scripts/rec/` に置く（git 管理外）。録画は `clip_crop` で必要な部分だけ切り出す。
- テロップは1行8〜10文字で改行する。
