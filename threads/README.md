# Threads 自動投稿

`threads/queue/` に投稿文のファイルを置くと、GitHub Actions が決まった時間に1件ずつ Threads に投稿します。
投稿にはThreadsの公式APIを使います。外部の予約投稿ツールは使いません。

```
threads/queue/ に投稿文を置く
   ↓（日本時間 7:30 / 12:15 / 20:30 に GitHub Actions が起動）
いちばん古い1件を Threads API で投稿
   ↓
threads/posted/ に移動（投稿日時と投稿IDを記録）
```

## 投稿文の置き方

1ファイルに1投稿を書きます。拡張子は `.md` か `.txt` です。本文の上限は500文字です。

| ファイル名 | いつ投稿されるか |
|---|---|
| `001_day16.md` | 次の投稿枠（日時指定なしのファイルは名前順） |
| `2026-10-05_0800_day16.md` | 10/5 8:00（日本時間）以降の最初の投稿枠 |
| `_draft.md` | 投稿されない（`_` で始まるファイルは下書き扱い） |

- 1回の実行で投稿するのは1件だけです。
- 日時指定のファイルで期限が来ているものは、日時指定なしのファイルより先に投稿されます。
- 投稿時刻を変えたい場合は `.github/workflows/threads-autopost.yml` の `cron` を編集します（UTCで書くので、日本時間から9時間引きます）。

手元でキューを確認するには次のコマンドを使います。

```bash
python3 threads/autopost.py check            # 文字数チェックと投稿順の確認
python3 threads/autopost.py post --dry-run   # 次に投稿される内容を表示（投稿はしない）
```

## 初期設定（最初に1回だけ）

### 1. Meta の開発者アプリを作る

1. https://developers.facebook.com/apps/ で「アプリを作成」を押す。
2. ユースケースで「Threads API にアクセス」を選ぶ。
3. 「ユースケース」→「Threads API」→「設定」で、権限 `threads_basic` と `threads_content_publish` を追加する。
4. 「役割」→「Threads テスター」に、自分の Threads アカウント（@zero_ai_challenge365）を追加する。
5. Threads アプリ（Web版でも可）の「設定」→「アカウント」→「ウェブサイトのアクセス許可」→「招待」から、テスターの招待を承認する。

自分のアカウントだけに投稿する場合、アプリの審査（公開）は不要です。

### 2. 長期アクセストークンを取る

1. Meta の開発者画面の「Threads API」→「ユーザートークン生成ツール」（または Graph API エクスプローラーで `graph.threads.net` を選択）で、自分のアカウントのアクセストークンを発行する。
2. 発行されるトークンは短期（1時間）の場合があります。その場合は、次のURLをブラウザで開いて長期トークン（60日）に交換します。

   ```
   https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=【アプリシークレット】&access_token=【短期トークン】
   ```

   アプリシークレットは「アプリの設定」→「ベーシック」→「Threads アプリシークレット」にあります。

### 3. GitHub に Secret を登録する

リポジトリの Settings → Secrets and variables → Actions → New repository secret で次を登録します。

| 名前 | 中身 | 必須 |
|---|---|---|
| `THREADS_ACCESS_TOKEN` | 手順2の長期アクセストークン | 必須 |
| `THREADS_USER_ID` | Threads のユーザーID（数字） | 任意（省略すると自動取得） |
| `GH_PAT` | トークン自動更新用の Personal Access Token（下記） | 推奨 |

**GH_PAT の作り方**：GitHub の Settings → Developer settings → Personal access tokens → Fine-grained tokens で、
対象リポジトリを `my-first-project` だけに絞り、権限「Secrets: Read and write」を付けて作成します。
これがあると、`Threads トークン更新` ワークフローが毎月1日と15日にトークンを自動で延長します。
GH_PAT を登録しない場合は、60日ごとに手順2をやり直して `THREADS_ACCESS_TOKEN` を差し替えてください。

### 4. 動作確認

1. GitHub の Actions タブ →「Threads 自動投稿」→「Run workflow」で `dry_run` にチェックを入れて実行すると、投稿せずに内容だけ確認できます。
2. 問題がなければ、チェックを外して実行すると実際に投稿されます。

> GitHub Actions の定期実行（schedule）は、デフォルトブランチ（main）にあるワークフローでしか動きません。このブランチを main にマージしてから使ってください。

## うまくいかないとき

| 症状 | 原因と対処 |
|---|---|
| `THREADS_ACCESS_TOKEN が設定されていません` | Secret の名前が違うか、未登録です。 |
| `HTTP 400 ... Session has expired` / `Error validating access token` | トークンの期限切れです。初期設定の手順2をやり直してください。 |
| `HTTP 403` / 権限エラー | `threads_content_publish` の権限、またはテスター招待の承認が抜けています。 |
| `500文字あります` | 本文を500文字以内に収めてください。 |
| 予定の時刻より遅れて投稿される | GitHub Actions の混雑による遅れで、数分〜数十分ずれることがあります。 |
