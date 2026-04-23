# meeting-note

会議議事録構造化ツール — 音声録音や会議ツールの文字起こしから Vertex AI Gemini で
構造化データを抽出し、Markdown や HTML にコンパイルします。

## 特徴

- **構造化抽出**: 音声や文字起こしから、議題・意思決定（根拠付き）・アクションアイテム・参加者間の関係性などを含む構造化JSONを生成
- **ドキュメントコンパイル**: 構造化JSONからMarkdownまたは自己完結型HTMLを生成
- **意思決定の追跡**: 「何が決まったか」だけでなく「なぜそう決まったか」を記録（検討された代替案と棄却理由を含む）
- **参加者間の関係性分析**: 提案→承認、委任、質疑応答などの関係性を分析
- **柔軟な入力**: 音声ファイル、文字起こしテキスト、または両方を受け付け

## 前提条件

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) パッケージマネージャ
- Vertex AI API が有効な Google Cloud プロジェクト
- Application Default Credentials の設定:
  ```bash
  gcloud auth application-default login
  ```

## インストール

```bash
git clone https://github.com/nlink-jp/meeting-note.git
cd meeting-note
uv sync
```

## 設定

meeting-note は複数の設定ソースから構成を読み込みます。優先順位は以下の通りです:

1. **CLIフラグ**（最優先）
2. **環境変数**
3. **`.env` ファイル**（カレントディレクトリ）
4. **TOML設定ファイル**（`~/.config/meeting-note/config.toml`）
5. **ビルトインデフォルト**（最低優先）

### 設定ファイルのセットアップ

`~/.config/meeting-note/config.toml` を作成:

```toml
project = "your-gcp-project-id"
location = "us-central1"
model = "gemini-2.5-flash"
max_output_tokens = 65536
```

完全な例は `config.example.toml` を参照してください。

### 環境変数

環境変数を設定（または `.env` ファイルを作成）:

```bash
MEETING_NOTE_PROJECT=your-gcp-project-id    # 必須
MEETING_NOTE_LOCATION=us-central1           # デフォルト
MEETING_NOTE_MODEL=gemini-2.5-flash         # デフォルト
MEETING_NOTE_MAX_OUTPUT_TOKENS=65536        # デフォルト
MEETING_NOTE_GCS_AUDIO_BUCKET=your-bucket  # 音声入力(-a)に必須
```

> **注意:** 音声入力（`-a`）にはGCSバケットの設定が必要です。
> テキスト/VTTトランスクリプトのみの場合はGCS不要です。
> アップロードされた音声ファイルは処理後に自動削除されます。

## 使い方

### 会議から構造化データを抽出

```bash
# 音声 + 文字起こし
meeting-note ingest -a meeting.mp3 -t transcript.txt -o meeting.json

# 音声のみ
meeting-note ingest -a meeting.mp3 -o meeting.json

# 文字起こしのみ
meeting-note ingest -t transcript.txt -o meeting.json

# 話者ヒント付き（話者ラベルのない文字起こしで話者特定を補助）
meeting-note ingest -t transcript.txt -p '田中,佐藤,鈴木' -o meeting.json

# 出力言語を指定（省略時は入力テキストから自動検出）
meeting-note ingest -t transcript.txt --lang ja -o meeting.json
```

### ドキュメントにコンパイル

```bash
# Markdown（デフォルト）
meeting-note compile meeting.json -o meeting.md

# HTML（自己完結型）
meeting-note compile meeting.json -f html -o meeting.html
```

## ビルド

```bash
make build    # パッケージをdist/にビルド
make test     # テスト実行
make lint     # リンター実行
```

## ドキュメント

- [データ構造定義書](docs/ja/data-format.md) — 構造化JSONスキーマリファレンス
- [アーキテクチャと処理方式](docs/ja/architecture.md) — パイプライン、プロンプト設計、セキュリティ
- [設計ドキュメント](docs/design/planning.md)
- [JSONスキーマ](docs/design/schema.json)
- [English documentation](README.md)

## ライセンス

MIT
