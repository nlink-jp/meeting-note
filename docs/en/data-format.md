# Data Format Specification

This document defines the structured JSON format output by `meeting-note ingest`
and consumed by `meeting-note compile`.

## Overview

The MeetingNote JSON is designed to be a **self-contained, reusable data source**.
It captures not just what was discussed, but *why* decisions were made, *who*
influenced them, and *what* the original speakers actually said.

```
MeetingNote
├── Meeting identification (id, title, date, type, context)
├── Participants[] (name, role, affiliation)
├── ParticipantDynamics[] (from → to, relation type)
├── Agenda[]
│   ├── Status (decided / pending / rejected / informational)
│   ├── Utterances[] (speaker, verbatim text)  ← raw evidence
│   ├── Discussion points[]                     ← summarized
│   ├── Decisions[] (what, WHY, alternatives)   ← structured
│   ├── ActionItems[] (owner, task, due)
│   └── Unresolved[] (issue, blocker)
├── Key takeaways[]
├── raw_transcript                              ← full original text
└── Metadata (source files, generator, model)
```

## Root: MeetingNote

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `meeting_id` | string | auto | Unique ID. Auto-generated as SHA-256(title+date)[:12] if empty |
| `title` | string | yes | Meeting title |
| `date` | ISO 8601 datetime | yes | Meeting start date/time |
| `duration_seconds` | integer | no | Duration in seconds |
| `meeting_type` | enum | no | `regular` / `ad_hoc` / `review` / `decision` / `informational` |
| `context` | string | no | Project or background this meeting relates to |
| `participants` | Participant[] | no | List of attendees |
| `participant_dynamics` | ParticipantDynamics[] | no | Directional relationships between participants |
| `agenda` | AgendaItem[] | no | Topics discussed |
| `key_takeaways` | string[] | no | 3-5 meeting-level summary points |
| `raw_transcript` | string | no | Full original transcript text. Populated by meeting-note (not LLM) to preserve source material |
| `metadata` | MeetingMetadata | no | Generation metadata |

## Participant

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Speaker name |
| `role` | enum | no | `organizer` / `decision_maker` / `proposer` / `reporter` / `observer` |
| `affiliation` | string | no | Team, department, or title |

### Role definitions

| Value | Description |
|-------|-------------|
| `organizer` | Chairs the meeting, sets agenda, manages flow |
| `decision_maker` | Has authority to approve or reject proposals |
| `proposer` | Presents ideas, proposals, or alternatives |
| `reporter` | Provides status updates or factual information |
| `observer` | Listens without active contribution |

## ParticipantDynamics

Captures **directional** relationships observed during the meeting.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from` | string | yes | Person initiating the interaction |
| `to` | string | yes | Person receiving the interaction |
| `relation` | enum | yes | Type of relationship (see below) |
| `topic` | string | no | Related agenda item title |
| `detail` | string | no | Specific description of the interaction |

### Relation types

| Value | Description | Example |
|-------|-------------|---------|
| `proposal_approval` | One proposes, another approves | "Suzuki proposed Option B, Sato approved" |
| `objection_reproposal` | One objects, leading to a revised proposal | "Tanaka objected to timeline, Suzuki revised" |
| `delegation` | One assigns work to another | "Manager delegated investigation to analyst" |
| `question_answer` | One asks, another answers | "Legal asked about data residency, Infra answered" |
| `report` | One reports status/findings to another | "SOC analyst reported incident timeline to CISO" |
| `instruction` | One gives directives to another | "Chair instructed to prepare cost comparison" |

## AgendaItem

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Topic title |
| `status` | enum | yes | `decided` / `pending` / `rejected` / `informational` |
| `summary` | string | no | LLM-generated summary of the discussion |
| `speakers` | string[] | no | Names of people who spoke on this topic |
| `utterances` | Utterance[] | no | Raw speaker-attributed statements (see below) |
| `discussion_points` | string[] | no | Key points discussed (summarized) |
| `decisions` | Decision[] | no | Decisions made on this topic |
| `action_items` | ActionItem[] | no | Tasks assigned |
| `unresolved` | UnresolvedItem[] | no | Issues carried forward |

### Status definitions

| Value | Description |
|-------|-------------|
| `decided` | A conclusion was reached and agreed upon |
| `pending` | Discussion occurred but no conclusion; carried forward |
| `rejected` | A proposal was explicitly rejected |
| `informational` | Information sharing only; no decision required |

## Utterance

Preserves **raw speaker-attributed statements** relevant to each agenda item.
These serve as primary evidence even after audio/transcript files are deleted.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `speaker` | string | yes | Name of the person who spoke |
| `text` | string | yes | Verbatim or near-verbatim text of the statement |
| `timestamp` | string | no | Time within the meeting (if available from source) |

## Decision

The core differentiator of this format: decisions include **rationale**.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `what` | string | yes | What was decided |
| `why` | string | yes | **Why** this decision was made (rationale) |
| `alternatives_considered` | Alternative[] | no | Other options that were discussed |
| `decided_by` | string[] | no | Names of people who made or approved the decision |

### Alternative

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `option` | string | yes | The alternative that was considered |
| `rejected_because` | string | yes | Why it was rejected |

## ActionItem

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `owner` | string | yes | Person responsible |
| `task` | string | yes | Task description |
| `due` | string | no | Deadline (free text, e.g. "4月17日", "next Friday") |
| `context` | string | no | Which decision or discussion this originated from |

## UnresolvedItem

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `issue` | string | yes | What remains unresolved |
| `blocker` | string | no | What is preventing resolution |
| `carry_forward_to` | string | no | Where this will be addressed (e.g. "next meeting") |

## MeetingMetadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_audio` | string | no | Original audio filename |
| `source_transcript` | string | no | "provided" if transcript was given |
| `generated_by` | string | yes | Tool and version (e.g. "meeting-note v0.1.0") |
| `generated_at` | ISO 8601 datetime | yes | Generation timestamp (UTC) |
| `model` | string | yes | LLM model used (e.g. "gemini-2.5-flash") |

## Data layers

The JSON contains three layers of information at different abstraction levels:

| Layer | Fields | Purpose |
|-------|--------|---------|
| **Raw** | `raw_transcript`, `utterances[]` | Original source material. Preserved verbatim for archival and traceability |
| **Structured** | `decisions[]`, `action_items[]`, `unresolved[]`, `participant_dynamics[]` | Machine-queryable facts extracted by LLM |
| **Summarized** | `summary`, `discussion_points[]`, `key_takeaways[]` | Human-readable condensation |

This layering ensures the JSON is useful both as a **database record** (structured layer)
and as a **source of truth** (raw layer) even after original files are deleted.

## LLM output normalization

Pydantic field validators handle common LLM output quirks:

| Input | Normalized to | Applied on |
|-------|--------------|------------|
| `null` / `None` | `""` (empty string) | All string fields in Decision, ActionItem, UnresolvedItem, Utterance |
| `["a", "b"]` (list) | `"a\nb"` (joined) | All string fields in Decision, ActionItem, UnresolvedItem, Utterance |
| Empty `meeting_id` | SHA-256(title+date)[:12] | MeetingNote model validator |
