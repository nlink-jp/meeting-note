# meeting-note — Planning Document

## 1. Problem Statement

Meeting records are typically stored as unstructured documents, making them
difficult to reuse, search, and cross-reference. This tool uses multimodal LLM
(Vertex AI Gemini) to extract structured JSON from audio recordings and/or
transcripts, then compiles human-readable documents (Markdown, HTML) from that
structured data.

Target users: teams that want to treat meeting records as queryable, reusable
data sources rather than static documents.

## 2. Functional Specification

### Commands

```
meeting-note ingest  -a audio.mp3 -t transcript.txt -o meeting.json
meeting-note compile meeting.json [-f markdown|html] [-o output.md]
```

### Input

- Audio files (mp3, wav, m4a, etc.) — analyzed via Gemini multimodal
- Transcript text (txt, srt, vtt, json) — meeting tool output
- Either one or both may be provided

### Structured JSON Schema

See `docs/design/schema.json` for the full schema definition.

Key elements:
- **Meeting identification**: id, title, date, duration, type, context
- **Participants**: name, role (organizer/decision-maker/proposer/reporter/observer), affiliation
- **Participant dynamics**: directional relationships (proposal→approval, objection→re-proposal, delegation, Q&A)
- **Agenda items** with status tracking (decided/pending/rejected/informational):
  - Discussion points and speaker attribution
  - Decisions with **why** (rationale) and alternatives considered (with rejection reasons)
  - Action items with owner, task, due date, and originating context
  - Unresolved issues with blockers and carry-forward targets
- **Key takeaways**: meeting-level summary points
- **Metadata**: source files, generation info, model used

### Output

- `ingest` → structured JSON file
- `compile` → Markdown or self-contained HTML

## 3. Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python | Gemini multimodal + google-genai SDK affinity; consistent with ai-ir2 |
| LLM | Vertex AI Gemini | Multimodal (audio+text), JSON schema output, embedding API |
| Auth | ADC | No service account needed; works locally and on Cloud Run |
| SDK | google-genai | vertexai SDK is deprecated |
| Data format | JSON | LLM JSON schema output; pipe-friendly with existing util-series tools |
| CLI framework | Click | Consistent with ai-ir2 |
| Config | pydantic-settings | Env var + .env + CLI override pattern |
| HTML rendering | Jinja2 | Self-contained HTML (inline CSS/JS), proven in ai-ir2 |
| Out of scope | Real-time processing, video analysis, storage/embedding/search | Future phases |

## 4. Development Plan

### Phase 1: Core — ingest + structured JSON generation (current)
- Gemini multimodal audio/text → structured JSON
- JSON schema definition and Pydantic models
- Tests with mockable LLM client

### Phase 2: Compile — document generation (current)
- Structured JSON → Markdown
- Structured JSON → self-contained HTML
- Template system

### Phase 3: Storage + Embedding (future)
- SQLite schema, JSON storage, normalized tables
- Gemini embedding API, vector storage
- Semantic search, meeting similarity

## 5. Required API Scopes

| Service | Permission |
|---------|-----------|
| Vertex AI | `aiplatform.endpoints.predict` (Gemini generation) |
| ADC | `gcloud auth application-default login` for local auth |

## 6. Series Placement

**lab-series** — PoC/PoV phase. May move to util-series or a new series after stabilization.

## 7. External Platform Constraints

- **Gemini audio input**: Inline data ≤20 MB; use Files API for larger files
- **Gemini JSON output**: `response_schema` parameter for structured output
- **Rate limits**: Vertex AI per-project quotas apply
