# meeting-note

Meeting minutes structuring tool — audio/transcript to structured JSON, then compile to Markdown/HTML.

- **Language**: Python 3.11+ / uv
- **LLM**: Vertex AI Gemini (google-genai SDK, ADC auth)
- **Series**: lab-series
- **CLI**: `meeting-note ingest -a audio.mp3 -t transcript.txt -o meeting.json`
- **CLI**: `meeting-note compile meeting.json [-f markdown|html] [-o output.md]`
- **Input**: Audio files (mp3/wav/m4a) and/or meeting tool transcripts (txt/srt/vtt/json)
- **Output**: Structured JSON → Markdown / self-contained HTML
- **Build**: `uv build --out-dir dist/` via `make build`
- **Test**: `uv run pytest tests/ -v` via `make test`
- **Module path**: `src/meeting_note/`
