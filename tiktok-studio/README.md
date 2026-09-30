# tiktok-studio

台本（JSONファイル）を書くだけで、TikTok 用の縦型テロップ動画（1080×1920）を作るツールです。
顔出し・声出しなしで投稿することを前提にしています。

- 大きいテロップが下からふわっと出るアニメーション
- `**ここ**` と書いた部分を強調色で表示
- 画面録画（mp4）やスクリーンショットをはめ込める
- プロンプトを見せるための「コード枠」
- 画面上部の進捗バー（最後まで見てもらいやすくする工夫）
- 字幕ファイル（.srt）も同時に作成
- `--photos` でフォトモード用の画像（PNG）を書き出し
- BGM や、CapCut などで作った読み上げ音声を合成

## 1. 準備（最初の1回だけ）

Python 3.9 以上が入っていれば OK です。ffmpeg も自動で入ります。

```bash
cd tiktok-studio
pip install -r requirements.txt
```

## 2. 動画を作る

```bash
python3 make_video.py scripts/sample_build.json
```

`out/sample_build.mp4` ができます。複数まとめて作ることもできます。

```bash
python3 make_video.py scripts/*.json
```

フォトモード（画像を横にめくる投稿）用の画像を書き出す場合:

```bash
python3 make_video.py scripts/sample_prompts.json --photos
```

## 3. 台本の書き方

```json
{
  "handle": "@your_account",
  "series": "AIに作らせてみた #1",
  "theme": "dark",
  "scenes": [
    {"style": "hook", "text": "AIに\n「**ゲーム作って**」\nって言っただけの結果…"},
    {"label": "AIへの指示はこれだけ", "code": "落ちものパズルゲームを作って。", "text": ""},
    {"text": "作っている様子（**4倍速**）", "clip": "rec.mp4", "clip_speed": 4},
    {"text": "完成したゲーム", "image": "screenshot.png"},
    {"style": "cta", "text": "次は何を作らせる？\n**コメントで募集中**"}
  ]
}
```

### 全体の設定

| 項目 | 意味 |
|---|---|
| `handle` | 自分のアカウント名。右上と最後のシーンに表示されます |
| `series` | シリーズ名。左上に表示されます（なくてもOK） |
| `theme` | `dark` / `light` / `pop` / `green` |
| `progress_bar` | 上部の進捗バー。`false` で消せます |
| `page_numbers` | `true` で「1 / 7」のようなページ番号を表示（フォトモード向け） |
| `bgm` / `bgm_volume` | BGM のファイルと音量（初期値 0.15）。短い曲は繰り返し再生されます |
| `voice` / `voice_volume` | 読み上げ音声のファイルと音量 |

### シーンの設定

| 項目 | 意味 |
|---|---|
| `text` | テロップ。`\n` で改行、`**強調**` で色が変わります |
| `style` | `hook`（最初の特大テロップ）/ `normal` / `cta`（最後のフォロー誘導） |
| `label` | テロップの上に出る小さい見出し（例:「① メールを速く書く」） |
| `code` | プロンプトなどを枠の中に表示します |
| `clip` | 画面録画の mp4。`clip_speed`（倍速）、`clip_start`（開始秒）、`clip_max`（最大秒数、初期値12）も指定できます |
| `image` | スクリーンショットなどの画像 |
| `duration` | 表示秒数。書かなければ文字数から自動で決まります |
| `animate` | `false` でテロップのアニメーションを止めます |

ファイルの場所は、台本のJSONがあるフォルダを基準に書きます。

### きれいに見せるコツ

- **1行は8〜10文字**を目安に、自分で `\n` を入れて改行してください。長い行があると全体の文字が小さくなります。
- 最初のシーン（hook）は **1.5秒以内に読める長さ**にします。
- 画面の下の方は TikTok のキャプションと重なるので、ツール側で空けてあります。

## 4. 毎日の流れ（30〜45分）

1. `prompts/chatgpt_prompts.md` の「台本JSONを作る」プロンプトを ChatGPT に貼り、`content/ideas_50.md` からその日のネタを渡す（5分）
2. 出てきた JSON を `scripts/2026-10-01.json` などの名前で保存
3. 必要なら画面録画を撮る。Mac は `Cmd+Shift+5`、Windows は `Win+Alt+R`（10分）
4. `python3 make_video.py scripts/2026-10-01.json`（1分）
5. できた mp4 を CapCut に入れて、読み上げ音声・BGM・流行りの音源を付ける（10分）
6. TikTok に投稿。キャプションとハッシュタグは台本と一緒に ChatGPT に作らせる（5分）

## 5. 音声について

このツールは声を作りません。声を付ける方法は次のどちらかです。

- **CapCut の「テキスト読み上げ」**：`out/*.srt` の字幕を読み込ませると、テロップと同じタイミングで読み上げを作れます。
- **TikTok アプリ内の読み上げ機能**：投稿時にテキストを選び、「読み上げ」を押します。

作った音声ファイルを台本の `voice` に指定すれば、このツールで合成することもできます。

## 注意

- AI で作ったリアルな人物や風景の映像を使うときは、TikTok の「AI生成コンテンツ」ラベルを付けてください。
- BGM は TikTok 内の音源か、商用利用できる音源を使ってください。
