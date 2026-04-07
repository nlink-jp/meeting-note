"""Tests for meeting-note CLI."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from meeting_note.cli import main
from meeting_note.models import MeetingNote


class TestCLI:
    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "meeting-note" in result.output

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "ingest" in result.output
        assert "compile" in result.output

    def test_ingest_requires_input(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["ingest"])
        assert result.exit_code != 0
        assert "At least one of --audio or --transcript is required" in result.output

    def test_compile_requires_input(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["compile"])
        assert result.exit_code != 0


class TestIngestCommand:
    @patch("meeting_note.cli.GeminiClient")
    @patch("meeting_note.cli.analyze_meeting")
    @patch("meeting_note.cli.get_gemini_config")
    def test_ingest_with_transcript(
        self, mock_get_config: MagicMock, mock_analyze: MagicMock, mock_client_cls: MagicMock, tmp_path: Path
    ) -> None:
        transcript = tmp_path / "meeting.txt"
        transcript.write_text("Speaker A: Hello\nSpeaker B: Hi", encoding="utf-8")
        output = tmp_path / "meeting.json"

        sample_note = MeetingNote(title="Test Meeting", date="2026-04-07T10:00:00+09:00")
        mock_analyze.return_value = sample_note
        mock_get_config.return_value = MagicMock()

        runner = CliRunner()
        result = runner.invoke(main, ["ingest", "-t", str(transcript), "-o", str(output)])

        assert result.exit_code == 0, result.output
        assert output.exists()
        data = json.loads(output.read_text())
        assert data["title"] == "Test Meeting"
        mock_analyze.assert_called_once()

    @patch("meeting_note.cli.GeminiClient")
    @patch("meeting_note.cli.analyze_meeting")
    @patch("meeting_note.cli.get_gemini_config")
    def test_ingest_default_output_path(
        self, mock_get_config: MagicMock, mock_analyze: MagicMock, mock_client_cls: MagicMock, tmp_path: Path
    ) -> None:
        transcript = tmp_path / "sprint-planning.txt"
        transcript.write_text("Discussion content", encoding="utf-8")

        sample_note = MeetingNote(title="Sprint Planning", date="2026-04-07T10:00:00+09:00")
        mock_analyze.return_value = sample_note
        mock_get_config.return_value = MagicMock()

        runner = CliRunner()
        result = runner.invoke(main, ["ingest", "-t", str(transcript)])

        assert result.exit_code == 0, result.output
        expected = tmp_path / "sprint-planning.json"
        assert expected.exists()

    @patch("meeting_note.cli.get_gemini_config", side_effect=ValueError("GCP project ID is required"))
    def test_ingest_missing_project_error(self, mock_get_config: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["ingest", "-t", "/dev/null"])
        assert result.exit_code != 0
        assert "GCP project ID is required" in result.output


class TestCompileCommand:
    def test_compile_markdown(self, tmp_path: Path, sample_meeting_note: MeetingNote) -> None:
        input_json = tmp_path / "meeting.json"
        input_json.write_text(sample_meeting_note.model_dump_json(by_alias=True, indent=2), encoding="utf-8")
        output = tmp_path / "meeting.md"

        runner = CliRunner()
        result = runner.invoke(main, ["compile", str(input_json), "-f", "markdown", "-o", str(output)])

        assert result.exit_code == 0, result.output
        content = output.read_text()
        assert "# Sprint Planning Meeting" in content

    def test_compile_html(self, tmp_path: Path, sample_meeting_note: MeetingNote) -> None:
        input_json = tmp_path / "meeting.json"
        input_json.write_text(sample_meeting_note.model_dump_json(by_alias=True, indent=2), encoding="utf-8")
        output = tmp_path / "meeting.html"

        runner = CliRunner()
        result = runner.invoke(main, ["compile", str(input_json), "-f", "html", "-o", str(output)])

        assert result.exit_code == 0, result.output
        content = output.read_text()
        assert "<!DOCTYPE html>" in content
        assert "Sprint Planning Meeting" in content

    def test_compile_default_output_path(self, tmp_path: Path, sample_meeting_note: MeetingNote) -> None:
        input_json = tmp_path / "sprint.json"
        input_json.write_text(sample_meeting_note.model_dump_json(by_alias=True, indent=2), encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(main, ["compile", str(input_json)])

        assert result.exit_code == 0, result.output
        expected = tmp_path / "sprint.md"
        assert expected.exists()

    def test_compile_invalid_json(self, tmp_path: Path) -> None:
        input_json = tmp_path / "bad.json"
        input_json.write_text('{"not": "a meeting"}', encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(main, ["compile", str(input_json)])

        assert result.exit_code != 0
        assert "Failed to parse" in result.output
