"""Tests for meeting-note CLI."""

from click.testing import CliRunner

from meeting_note.cli import main


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
