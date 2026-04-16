# meeting-note

Meeting minutes structuring tool — extract structured data from audio recordings
and meeting transcripts via Vertex AI Gemini, then compile into Markdown or HTML.

## Features

- **Structured extraction**: Converts audio and/or transcript into structured JSON
  with topics, decisions (with rationale), action items, participant dynamics, and more
- **Document compilation**: Generates Markdown or self-contained HTML from structured JSON
- **Decision tracking**: Captures not just *what* was decided, but *why*, including
  alternatives considered and rejection reasons
- **Participant dynamics**: Analyzes relationships between participants
  (proposal→approval, delegation, Q&A, etc.)
- **Flexible input**: Accepts audio files, transcript text, or both

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Cloud project with Vertex AI API enabled
- Application Default Credentials configured:
  ```bash
  gcloud auth application-default login
  ```

## Installation

```bash
git clone https://github.com/nlink-jp/meeting-note.git
cd meeting-note
uv sync
```

## Configuration

meeting-note reads configuration from multiple sources. The priority order is:

1. **CLI flags** (highest priority)
2. **Environment variables**
3. **`.env` file** in the current directory
4. **TOML config file** (`~/.config/meeting-note/config.toml`)
5. **Built-in defaults** (lowest priority)

### Config file setup

Create `~/.config/meeting-note/config.toml`:

```toml
project = "your-gcp-project-id"
location = "us-central1"
model = "gemini-2.5-flash"
max_output_tokens = 65536
```

See `config.example.toml` for a full example.

### Environment variables

Set environment variables (or create a `.env` file):

```bash
MEETING_NOTE_PROJECT=your-gcp-project-id    # Required
MEETING_NOTE_LOCATION=us-central1           # Default
MEETING_NOTE_MODEL=gemini-2.5-flash         # Default
MEETING_NOTE_MAX_OUTPUT_TOKENS=65536        # Default
MEETING_NOTE_GCS_AUDIO_BUCKET=your-bucket  # Required for audio input (-a)
```

> **Note:** Audio input (`-a`) requires a GCS bucket for temporary file upload.
> Text/VTT transcript-only usage does not require GCS.
> The uploaded audio file is automatically deleted after processing.

## Usage

### Extract structured data from a meeting

```bash
# From audio + transcript
meeting-note ingest -a meeting.mp3 -t transcript.txt -o meeting.json

# From audio only
meeting-note ingest -a meeting.mp3 -o meeting.json

# From transcript only
meeting-note ingest -t transcript.txt -o meeting.json

# With speaker hints (helps identify speakers in unlabeled transcripts)
meeting-note ingest -t transcript.txt -p 'Tanaka,Sato,Suzuki' -o meeting.json
```

### Compile into a document

```bash
# Markdown (default)
meeting-note compile meeting.json -o meeting.md

# HTML (self-contained)
meeting-note compile meeting.json -f html -o meeting.html
```

## Building

```bash
make build    # Build package to dist/
make test     # Run tests
make lint     # Run linter
```

## Documentation

- [Data Format Specification](docs/en/data-format.md) — structured JSON schema reference
- [Architecture and Processing](docs/en/architecture.md) — pipeline, prompt design, security
- [Planning Document](docs/design/planning.md)
- [JSON Schema](docs/design/schema.json)
- [日本語ドキュメント](README.ja.md)

## License

MIT
