# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

### Added

- `ingest` command: extract structured meeting data from audio and/or transcript via Gemini
  - Supports audio files (mp3, wav, m4a, ogg, flac, webm) via Files API
  - Supports transcript files (txt, srt, vtt, json) with format auto-detection
  - Prompt injection defense with nonce-tagged XML wrapping
  - Structured JSON output with MeetingNote schema
- `compile` command: generate documents from structured JSON
  - Markdown output with tables, decision rationale, status labels
  - Self-contained HTML with inline CSS/JS, status badges, collapsible agenda
- Pydantic data models with field validators for LLM output normalization
- Gemini LLM client with structured output parsing and retry with exponential backoff
- Configuration management via `MEETING_NOTE_*` environment variables (ADC auth)
- Design documents: planning.md, schema.json
