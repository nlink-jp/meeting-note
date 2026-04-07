"""Transcript file loading for various formats."""

from __future__ import annotations

import json
import re
from pathlib import Path

_SUPPORTED_EXTENSIONS = {".txt", ".srt", ".vtt", ".json"}

_SRT_TIMESTAMP = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}")
_VTT_TIMESTAMP = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}")
_SRT_INDEX = re.compile(r"^\d+$")


def load_transcript(path: Path) -> str:
    """Load transcript text from a file, dispatching by extension."""
    ext = path.suffix.lower()
    if ext not in _SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported transcript format: {ext} (supported: {', '.join(sorted(_SUPPORTED_EXTENSIONS))})")

    loaders = {
        ".txt": _load_txt,
        ".srt": _load_srt,
        ".vtt": _load_vtt,
        ".json": _load_json,
    }
    return loaders[ext](path)


def _load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_srt(path: Path) -> str:
    """Parse SRT format, stripping index and timing lines."""
    lines = path.read_text(encoding="utf-8").splitlines()
    text_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _SRT_INDEX.match(stripped):
            continue
        if _SRT_TIMESTAMP.match(stripped):
            continue
        text_lines.append(stripped)
    return "\n".join(text_lines)


def _load_vtt(path: Path) -> str:
    """Parse WebVTT format, stripping header and timing lines."""
    lines = path.read_text(encoding="utf-8").splitlines()
    text_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "WEBVTT":
            continue
        if _VTT_TIMESTAMP.match(stripped):
            continue
        if _SRT_INDEX.match(stripped):
            continue
        text_lines.append(stripped)
    return "\n".join(text_lines)


def _load_json(path: Path) -> str:
    """Load transcript from JSON — supports common formats."""
    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e

    # Empty array
    if isinstance(data, list) and not data:
        raise ValueError(f"Empty JSON array in {path}")

    # Array of objects with "text" key
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return "\n".join(item.get("text", str(item)) for item in data)

    # Array of strings
    if isinstance(data, list) and data and isinstance(data[0], str):
        return "\n".join(data)

    # Single object with "transcript" or "text" key
    if isinstance(data, dict):
        for key in ("transcript", "text", "content"):
            if key in data and isinstance(data[key], str):
                return data[key]
        # Object with segments array
        for key in ("segments", "results", "items"):
            if key in data and isinstance(data[key], list):
                segments = data[key]
                return "\n".join(
                    s.get("text", str(s)) if isinstance(s, dict) else str(s) for s in segments
                )

    raise ValueError(f"Cannot extract transcript from JSON structure in {path}")
