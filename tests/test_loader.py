"""Tests for transcript loader."""

import json
from pathlib import Path

import pytest

from meeting_note.ingest.loader import load_transcript


class TestLoadTxt:
    def test_plain_text(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.txt"
        f.write_text("Hello world\nSecond line", encoding="utf-8")
        result = load_transcript(f)
        assert result == "Hello world\nSecond line"


class TestLoadSrt:
    def test_strips_timing_and_index(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.srt"
        f.write_text(
            "1\n"
            "00:00:01,000 --> 00:00:03,000\n"
            "First subtitle\n"
            "\n"
            "2\n"
            "00:00:04,000 --> 00:00:06,000\n"
            "Second subtitle\n",
            encoding="utf-8",
        )
        result = load_transcript(f)
        assert result == "First subtitle\nSecond subtitle"

    def test_multiline_subtitle(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.srt"
        f.write_text(
            "1\n"
            "00:00:01,000 --> 00:00:03,000\n"
            "Line one\n"
            "Line two\n"
            "\n",
            encoding="utf-8",
        )
        result = load_transcript(f)
        assert "Line one" in result
        assert "Line two" in result


class TestLoadVtt:
    def test_strips_header_and_timing(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.vtt"
        f.write_text(
            "WEBVTT\n"
            "\n"
            "00:00:01.000 --> 00:00:03.000\n"
            "First cue\n"
            "\n"
            "00:00:04.000 --> 00:00:06.000\n"
            "Second cue\n",
            encoding="utf-8",
        )
        result = load_transcript(f)
        assert result == "First cue\nSecond cue"


class TestLoadJson:
    def test_array_of_objects(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.json"
        data = [{"text": "Hello"}, {"text": "World"}]
        f.write_text(json.dumps(data), encoding="utf-8")
        result = load_transcript(f)
        assert result == "Hello\nWorld"

    def test_array_of_strings(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.json"
        data = ["Line 1", "Line 2"]
        f.write_text(json.dumps(data), encoding="utf-8")
        result = load_transcript(f)
        assert result == "Line 1\nLine 2"

    def test_single_object_transcript_key(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.json"
        data = {"transcript": "Full transcript text here"}
        f.write_text(json.dumps(data), encoding="utf-8")
        result = load_transcript(f)
        assert result == "Full transcript text here"

    def test_single_object_segments(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.json"
        data = {"segments": [{"text": "Segment 1"}, {"text": "Segment 2"}]}
        f.write_text(json.dumps(data), encoding="utf-8")
        result = load_transcript(f)
        assert result == "Segment 1\nSegment 2"

    def test_unrecognized_structure_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.json"
        data = {"unknown_key": 42}
        f.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="Cannot extract transcript"):
            load_transcript(f)


class TestUnsupportedFormat:
    def test_pdf_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.pdf"
        f.write_text("dummy", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported transcript format"):
            load_transcript(f)
