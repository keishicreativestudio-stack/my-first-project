# my-first-project

TikTok（AI活用ジャンル／顔出しなし）で、1ヶ月でフォロワー1,000人を目指すための道具一式です。

| フォルダ | 中身 |
|---|---|
| [`content/`](content/) | 10/1〜10/30 の投稿ネタ50本（[一覧](content/ideas_50.md)・[記録用CSV](content/ideas_50.csv)）とフック30選 |
| [`tiktok-studio/`](tiktok-studio/) | 台本JSONから縦型テロップ動画を作るツール（[使い方](tiktok-studio/README.md)） |
| [`tiktok-studio/prompts/`](tiktok-studio/prompts/chatgpt_prompts.md) | 台本・フック・キャプション・振り返りに使う ChatGPT 用プロンプト |

## すぐ試す

```bash
cd tiktok-studio
pip install -r requirements.txt
python3 make_video.py scripts/sample_build.json
```
