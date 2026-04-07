# meeting-note Project Rules

## Purpose

Meeting minutes structuring tool. Extracts structured JSON from audio recordings
and/or meeting tool transcripts via Vertex AI Gemini, then compiles human-readable
documents (Markdown, self-contained HTML) from the structured data.

## Architecture

### Commands
```
meeting-note ingest  -a audio.mp3 -t transcript.txt -o meeting.json
meeting-note compile meeting.json [-f markdown|html] [-o output.md]
```

### Module Structure
```
src/meeting_note/
  __init__.py        - Version
  cli.py             - Click CLI: ingest + compile
  config.py          - GeminiConfig (project/location/model, ADC)
  models.py          - All Pydantic data models (MeetingNote schema)
  ingest/
    loader.py        - Transcript file loading (txt, srt, vtt, json)
    analyzer.py      - Meeting analysis orchestrator (system prompt, LLM call)
    sanitizer.py     - Prompt injection defense (nonce-tagged XML wrapping)
  compile/
    markdown.py      - Markdown renderer
    html.py          - HTML renderer (Jinja2)
    templates/
      report.html    - Self-contained HTML template (inline CSS/JS)
  llm/
    client.py        - Gemini client (structured output, retry, file upload)
```

## Security Rules

1. **No external transmission**: Only the configured Vertex AI Gemini endpoint
   may receive data. No analytics, telemetry, or third-party API calls.
2. **Prompt injection defense**: ALL user-sourced text (transcripts, audio
   transcriptions) MUST be processed through `sanitizer.sanitize_for_llm()`
   before LLM prompts. Uses nonce-tagged XML wrapping to isolate untrusted data.
3. **Uploaded file cleanup**: Audio files uploaded to Gemini Files API MUST be
   deleted immediately after processing (in a `finally` block).
4. **No secret logging**: API keys, tokens, and credentials must never appear
   in logs or output.
5. **Input validation**: All input files are validated against Pydantic models.

## Development Rules

- Small, focused modules — each file has a single clear responsibility
- Tests implemented alongside code in `tests/` directory
- Type hints required for all function signatures
- CHANGELOG.md updated on each feature addition
- No hardcoded credentials or endpoints
- Python with uv virtual environment (`uv sync` to install)
- Run tests: `uv run pytest tests/ -v`

## LLM Configuration

Configure via environment variables (or `.env` file):

```bash
MEETING_NOTE_PROJECT=your-gcp-project-id    # Required
MEETING_NOTE_LOCATION=us-central1           # Default
MEETING_NOTE_MODEL=gemini-2.5-flash         # Default
MEETING_NOTE_TIMEZONE=Asia/Tokyo            # Default
```

Authentication: Application Default Credentials (ADC).
Run `gcloud auth application-default login` to set up.

## Communication Language

All communication between contributors and Claude Code is conducted in **Japanese**.

## Release Procedure

1. Run tests: `uv run pytest tests/ -v`
2. Update `pyproject.toml` and `src/meeting_note/__init__.py` with version
3. Update CHANGELOG.md
4. Commit: `chore: release vX.Y.Z`
5. Tag: `git tag vX.Y.Z`
6. Push: `git push origin main --tags`
7. `gh release create vX.Y.Z` with **English** release notes
