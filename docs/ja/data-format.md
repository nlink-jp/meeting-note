# データ構造定義書

`meeting-note ingest` が出力し、`meeting-note compile` が入力として受け取る
構造化JSONフォーマットの定義書です。

## 概要

MeetingNote JSON は**自己完結型の再利用可能なデータソース**として設計されています。
議論の内容だけでなく、*なぜ*その決定に至ったか、*誰が*影響を与えたか、
*発言者が実際に何を言ったか*を保持します。

```
MeetingNote
├── 会議識別情報 (id, title, date, type, context)
├── Participants[] (氏名, 役割, 所属)
├── ParticipantDynamics[] (発信者 → 受信者, 関係種別)
├── Agenda[]
│   ├── Status (決定 / 保留 / 却下 / 情報共有)
│   ├── Utterances[] (発言者, 原文テキスト)   ← 生データ（証跡）
│   ├── Discussion points[]                    ← 要約
│   ├── Decisions[] (何を, なぜ, 代替案)      ← 構造化
│   ├── ActionItems[] (担当者, タスク, 期限)
│   └── Unresolved[] (課題, ブロッカー)
├── Key takeaways[]
├── raw_transcript                             ← 元テキスト全文
└── Metadata (ソースファイル, 生成情報, モデル)
```

## ルート: MeetingNote

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `meeting_id` | string | 自動 | 一意のID。空の場合 SHA-256(title+date)[:12] で自動生成 |
| `title` | string | はい | 会議タイトル |
| `date` | ISO 8601 datetime | はい | 会議開始日時 |
| `duration_seconds` | integer | いいえ | 所要時間（秒） |
| `meeting_type` | enum | いいえ | `regular`（定例）/ `ad_hoc`（臨時）/ `review` / `decision`（意思決定）/ `informational`（情報共有） |
| `context` | string | いいえ | この会議が属するプロジェクトや背景 |
| `participants` | Participant[] | いいえ | 参加者リスト |
| `participant_dynamics` | ParticipantDynamics[] | いいえ | 参加者間の方向性を持つ関係性 |
| `agenda` | AgendaItem[] | いいえ | 議論された議題 |
| `key_takeaways` | string[] | いいえ | 3〜5件の会議レベルのサマリーポイント |
| `raw_transcript` | string | いいえ | 元の文字起こし全文。meeting-noteが付与（LLMではない）。ソースファイル消失後の原文保全用 |
| `metadata` | MeetingMetadata | いいえ | 生成メタデータ |

## Participant（参加者）

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `name` | string | はい | 発言者名 |
| `role` | enum | いいえ | `organizer` / `decision_maker` / `proposer` / `reporter` / `observer` |
| `affiliation` | string | いいえ | チーム、部署、または肩書き |

### 役割の定義

| 値 | 表示名 | 説明 |
|----|--------|------|
| `organizer` | 主催者 | 会議を主催し、議題を設定し、進行を管理する |
| `decision_maker` | 意思決定者 | 提案を承認または却下する権限を持つ |
| `proposer` | 提案者 | アイデア、提案、または代替案を提示する |
| `reporter` | 報告者 | ステータス更新や事実情報を提供する |
| `observer` | オブザーバー | 積極的な貢献なしに傍聴する |

## ParticipantDynamics（参加者間の関係性）

会議中に観察された**方向性を持つ**関係性を記録します。

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `from` | string | はい | やりとりを開始した人 |
| `to` | string | はい | やりとりを受けた人 |
| `relation` | enum | はい | 関係の種類（下表参照） |
| `topic` | string | いいえ | 関連する議題タイトル |
| `detail` | string | いいえ | やりとりの具体的な説明 |

### 関係の種類

| 値 | 表示名 | 説明 | 例 |
|----|--------|------|-----|
| `proposal_approval` | 提案 → 承認 | 一方が提案し、他方が承認 | 「鈴木が案Bを提案し、佐藤が承認した」 |
| `objection_reproposal` | 反論 → 再提案 | 一方が反論し、修正案の提示に至る | 「田中がスケジュールに反論し、鈴木が修正した」 |
| `delegation` | 委任 | 一方が他方に作業を割り当てる | 「マネージャーが調査をアナリストに委任した」 |
| `question_answer` | 質疑応答 | 一方が質問し、他方が回答 | 「法務がデータ保管場所を質問し、インフラが回答した」 |
| `report` | 報告 | 一方が他方にステータス/調査結果を報告 | 「SOCアナリストがCISOにタイムラインを報告した」 |
| `instruction` | 指示 | 一方が他方に指示を出す | 「議長がコスト比較の準備を指示した」 |

## AgendaItem（議題）

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `title` | string | はい | 議題タイトル |
| `status` | enum | はい | `decided` / `pending` / `rejected` / `informational` |
| `summary` | string | いいえ | LLMが生成した議論の要約 |
| `speakers` | string[] | いいえ | この議題で発言した人の名前 |
| `utterances` | Utterance[] | いいえ | 発言者帰属付きの生発言（下記参照） |
| `discussion_points` | string[] | いいえ | 議論された主要ポイント（要約） |
| `decisions` | Decision[] | いいえ | この議題での決定事項 |
| `action_items` | ActionItem[] | いいえ | 割り当てられたタスク |
| `unresolved` | UnresolvedItem[] | いいえ | 持ち越された課題 |

### ステータスの定義

| 値 | 表示名 | 説明 |
|----|--------|------|
| `decided` | 決定 | 結論が出され、合意された |
| `pending` | 保留 | 議論されたが結論に至らず、持ち越し |
| `rejected` | 却下 | 提案が明示的に却下された |
| `informational` | 情報共有 | 情報共有のみ。決定は不要 |

## Utterance（発言）

各議題に関連する**発言者帰属付きの生発言**を保存します。
音声/文字起こしファイルが削除された後も、一次情報としての証跡を維持します。

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `speaker` | string | はい | 発言者名 |
| `text` | string | はい | 発言の逐語録またはそれに近いテキスト |
| `timestamp` | string | いいえ | 会議内の発言時刻（ソースから取得可能な場合） |

## Decision（決定事項）

本フォーマットの核心的差別化要素: 決定には**根拠（なぜ）**が含まれます。

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `what` | string | はい | 何が決まったか |
| `why` | string | はい | **なぜ**その決定に至ったか（根拠） |
| `alternatives_considered` | Alternative[] | いいえ | 検討された他の選択肢 |
| `decided_by` | string[] | いいえ | 決定に関与した人の名前 |

### Alternative（代替案）

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `option` | string | はい | 検討された代替案 |
| `rejected_because` | string | はい | 却下された理由 |

## ActionItem（アクションアイテム）

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `owner` | string | はい | 担当者 |
| `task` | string | はい | タスクの説明 |
| `due` | string | いいえ | 期限（自由テキスト。例: 「4月17日」「来週金曜」） |
| `context` | string | いいえ | どの決定・議論から発生したか |

## UnresolvedItem（未解決事項）

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `issue` | string | はい | 未解決の課題 |
| `blocker` | string | いいえ | 解決を妨げているもの |
| `carry_forward_to` | string | いいえ | どこで対処するか（例: 「次回会議」） |

## MeetingMetadata（メタデータ）

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `source_audio` | string | いいえ | 元の音声ファイル名 |
| `source_transcript` | string | いいえ | 文字起こしが提供された場合 "provided" |
| `generated_by` | string | はい | ツールとバージョン（例: "meeting-note v0.1.0"） |
| `generated_at` | ISO 8601 datetime | はい | 生成タイムスタンプ（UTC） |
| `model` | string | はい | 使用したLLMモデル（例: "gemini-2.5-flash"） |

## データレイヤー構造

JSONは異なる抽象度の3つのレイヤーで情報を保持します:

| レイヤー | フィールド | 目的 |
|----------|----------|------|
| **生データ** | `raw_transcript`, `utterances[]` | 元のソース素材。アーカイブとトレーサビリティのために逐語的に保存 |
| **構造化データ** | `decisions[]`, `action_items[]`, `unresolved[]`, `participant_dynamics[]` | LLMが抽出した機械検索可能なファクト |
| **要約** | `summary`, `discussion_points[]`, `key_takeaways[]` | 人間が読むための凝縮されたサマリー |

このレイヤー構造により、JSONは**データベースレコード**（構造化レイヤー）としても、
元ファイル削除後の**一次情報**（生データレイヤー）としても有用です。

## LLM出力の正規化

Pydanticのfield validatorがLLM出力の一般的な不整合を処理します:

| 入力 | 正規化後 | 適用対象 |
|------|---------|---------|
| `null` / `None` | `""`（空文字列） | Decision, ActionItem, UnresolvedItem, Utterance の全文字列フィールド |
| `["a", "b"]`（リスト） | `"a\nb"`（結合） | 同上 |
| 空の `meeting_id` | SHA-256(title+date)[:12] | MeetingNote モデルバリデータ |
