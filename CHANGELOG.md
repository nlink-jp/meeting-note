# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.9] - 2026-04-16

### Changed

- Increase API retry for large audio files: 5 retries with 5s base delay
  (5s → 10s → 20s → 40s → 80s, ~155s total backoff)

## [0.2.8] - 2026-04-16

### Fixed

- Fix audio file upload for Vertex AI: `files.upload()` is Developer API only,
  replaced with `Part.from_bytes()` inline data (no server-side file cleanup needed)

## [0.2.7] - 2026-04-16

### Fixed

- (incomplete fix — superseded by v0.2.8)

## [0.2.6] - 2026-04-15

### Fixed

- Auto-repair truncated/malformed JSON from Gemini using nlk/jsonfix — previously
  these errors were fatal, now the tool attempts repair before failing

### Added

- `nlk` (nlk-py) dependency for JSON repair (`jsonfix.extract`)

## [0.2.5] - 2026-04-14

### Added

- TOML config file support (`~/.config/meeting-note/config.toml`)
- Configuration priority: CLI flags > env vars > .env > config.toml > defaults

## [0.2.4] - 2026-04-13

### Fixed

- Catch truncated JSON before pydantic validation — Gemini may truncate output
  without setting `finish_reason=MAX_TOKENS`, so `complete_structured` now
  validates JSON well-formedness first and raises a clear `ValueError` with
  response length and `max_output_tokens` guidance

## [0.2.3] - 2026-04-13

### Fixed

- Set `max_output_tokens=65536` to prevent Gemini response truncation on long
  meetings — the root cause of `EOF while parsing a string` pydantic errors
- Detect `finish_reason=MAX_TOKENS` and raise a clear `ValueError` with guidance
  instead of letting truncated JSON propagate to pydantic validation

### Added

- `MEETING_NOTE_MAX_OUTPUT_TOKENS` environment variable to configure the output
  token limit (default: 65536)

## [0.2.2] - 2026-04-09

### Fixed

- Raise a descriptive `ValueError` (with `finish_reason`) when Gemini returns an
  empty response for structured output, instead of passing an empty string to
  `model_validate_json` and surfacing a confusing pydantic `EOF` error

## [0.2.1] - 2026-04-08

### Fixed

- Strengthen language preservation in system prompt — LLM no longer translates
  Japanese input into English output
- Set temperature to 0.2 for factual extraction — reduces hallucination and
  improves output consistency across repeated runs

## [0.2.0] - 2026-04-08

### Added

- `--known-participants` / `-p` option: pass comma-separated speaker names as hints
  to improve speaker identification when transcripts lack speaker labels
- Progress spinner (rich Status) for `ingest` and `compile` commands with
  step-by-step status messages

### Fixed

- Transcript loader now raises clear `ValueError` for broken JSON and empty arrays
- `.gitignore` pattern corrected for simulation output files

### Internal

- 14 edge case tests added for transcript loader (empty files, broken JSON,
  timing-only SRT/VTT, BOM-encoded UTF-8, null/bare-string JSON, HTML-tagged SRT)
- Test count: 112 → 126

## [0.1.0] - 2026-04-08

### Added

- `ingest` command: extract structured meeting data from audio and/or transcript via Gemini
  - Supports audio files (mp3, wav, m4a, ogg, flac, webm) via Files API
  - Supports transcript files (txt, srt, vtt, json) with format auto-detection
  - Prompt injection defense with nonce-tagged XML wrapping
  - Structured JSON output with MeetingNote schema
  - Raw transcript preservation (`raw_transcript` field)
  - Per-agenda utterance extraction with speaker attribution
- `compile` command: generate documents from structured JSON
  - Markdown output with Japanese-localized labels, decision rationale, status labels
  - Self-contained HTML with inline CSS/JS, status badges, collapsible agenda cards
  - Timezone-aware timestamp display (default: Asia/Tokyo)
- Pydantic data models with field validators for LLM output normalization
- Gemini LLM client with structured output parsing and retry with exponential backoff
- Configuration management via `MEETING_NOTE_*` environment variables (ADC auth)
- Data format specification and architecture documentation (en/ja)

### Security

- Nonce-tagged XML wrapping for prompt injection defense
- Immediate deletion of uploaded audio files after Gemini processing
- 14-pattern injection detection with warning logs
