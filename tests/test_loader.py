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


class TestEdgeCases:
    """Edge cases: empty files, broken formats, encoding issues."""

    def test_empty_txt(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        result = load_transcript(f)
        assert result == ""

    def test_empty_srt(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.srt"
        f.write_text("", encoding="utf-8")
        result = load_transcript(f)
        assert result == ""

    def test_empty_vtt(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.vtt"
        f.write_text("WEBVTT\n\n", encoding="utf-8")
        result = load_transcript(f)
        assert result == ""

    def test_srt_timing_only(self, tmp_path: Path) -> None:
        """SRT with timing lines but no text content."""
        f = tmp_path / "timing-only.srt"
        f.write_text(
            "1\n00:00:01,000 --> 00:00:03,000\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\n\n",
            encoding="utf-8",
        )
        result = load_transcript(f)
        assert result == ""

    def test_vtt_timing_only(self, tmp_path: Path) -> None:
        """VTT with header and timing but no cue text."""
        f = tmp_path / "timing-only.vtt"
        f.write_text(
            "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n\n",
            encoding="utf-8",
        )
        result = load_transcript(f)
        assert result == ""

    def test_broken_json(self, tmp_path: Path) -> None:
        f = tmp_path / "broken.json"
        f.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_transcript(f)

    def test_empty_json_array(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.json"
        f.write_text("[]", encoding="utf-8")
        with pytest.raises(ValueError, match="Empty JSON array"):
            load_transcript(f)

    def test_json_null(self, tmp_path: Path) -> None:
        f = tmp_path / "null.json"
        f.write_text("null", encoding="utf-8")
        with pytest.raises(ValueError, match="Cannot extract transcript"):
            load_transcript(f)

    def test_json_bare_string(self, tmp_path: Path) -> None:
        f = tmp_path / "bare.json"
        f.write_text('"just a string"', encoding="utf-8")
        with pytest.raises(ValueError, match="Cannot extract transcript"):
            load_transcript(f)

    def test_bom_utf8_txt(self, tmp_path: Path) -> None:
        """UTF-8 BOM should not corrupt content."""
        f = tmp_path / "bom.txt"
        f.write_bytes(b"\xef\xbb\xbfHello BOM")
        result = load_transcript(f)
        assert "Hello BOM" in result

    def test_srt_with_html_tags(self, tmp_path: Path) -> None:
        """SRT with HTML formatting tags (common in real files)."""
        f = tmp_path / "tagged.srt"
        f.write_text(
            "1\n00:00:01,000 --> 00:00:03,000\n<i>Italic text</i>\n\n",
            encoding="utf-8",
        )
        result = load_transcript(f)
        assert "<i>Italic text</i>" in result

    def test_file_not_found(self, tmp_path: Path) -> None:
        f = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            load_transcript(f)


class TestUnsupportedFormat:
    def test_pdf_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.pdf"
        f.write_text("dummy", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported transcript format"):
            load_transcript(f)
