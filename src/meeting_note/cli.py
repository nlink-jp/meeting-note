"""CLI entry point for meeting-note."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from meeting_note import __version__
from meeting_note.compile import render_html, render_markdown
from meeting_note.config import get_gemini_config
from meeting_note.ingest import analyze_meeting, load_transcript
from meeting_note.llm.client import GeminiClient
from meeting_note.models import MeetingNote

err = Console(stderr=True)


@click.group()
@click.version_option(version=__version__, prog_name="meeting-note")
def main() -> None:
    """Meeting minutes structuring tool."""
    pass


@main.command()
@click.option("--audio", "-a", type=click.Path(exists=True), help="Audio file (mp3, wav, m4a, etc.)")
@click.option("--transcript", "-t", type=click.Path(exists=True), help="Transcript file (txt, srt, vtt, json)")
@click.option("--output", "-o", default="", help="Output JSON file path")
@click.option("--project", default="", help="GCP project ID (overrides env)")
@click.option("--location", default="", help="GCP location (overrides env)")
@click.option("--model", default="", help="Gemini model name (overrides env)")
@click.option("--known-participants", "-p", default="", help="Comma-separated participant names as hints (e.g. 'Tanaka,Sato,Suzuki')")
def ingest(audio: str | None, transcript: str | None, output: str, project: str, location: str, model: str, known_participants: str) -> None:
    """Extract structured meeting data from audio and/or transcript."""
    if not audio and not transcript:
        raise click.UsageError("At least one of --audio or --transcript is required.")

    try:
        config = get_gemini_config(project=project, location=location, model=model)
    except ValueError as e:
        raise click.ClickException(str(e)) from e

    # Load transcript if provided
    transcript_text: str | None = None
    if transcript:
        err.print(f"Loading transcript: {transcript}")
        transcript_text = load_transcript(Path(transcript))

    # Create client and analyze
    err.print("Analyzing meeting via Gemini...")
    client = GeminiClient(config)
    # Parse participant hints
    participants: list[str] = []
    if known_participants:
        participants = [p.strip() for p in known_participants.split(",") if p.strip()]

    note = analyze_meeting(
        transcript=transcript_text,
        audio_path=audio,
        known_participants=participants,
        client=client,
        config=config,
    )

    # Determine output path
    if not output:
        if transcript:
            output = str(Path(transcript).with_suffix(".json"))
        elif audio:
            output = str(Path(audio).with_suffix(".json"))
        else:
            output = "meeting.json"

    # Write output
    Path(output).write_text(
        note.model_dump_json(by_alias=True, indent=2),
        encoding="utf-8",
    )
    err.print(f"[green]Wrote structured meeting data to {output}[/green]")


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--format", "-f", "fmt", type=click.Choice(["markdown", "html"]), default="markdown", help="Output format")
@click.option("--output", "-o", default="", help="Output file path")
@click.option("--timezone", "-z", default="Asia/Tokyo", help="Timezone for display (IANA name)")
def compile(input_file: str, fmt: str, output: str, timezone: str) -> None:
    """Compile structured JSON into Markdown or HTML."""
    input_path = Path(input_file)

    try:
        note = MeetingNote.model_validate_json(input_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise click.ClickException(f"Failed to parse {input_file}: {e}") from e

    if fmt == "html":
        content = render_html(note, tz=timezone)
        default_ext = ".html"
    else:
        content = render_markdown(note, tz=timezone)
        default_ext = ".md"

    if not output:
        output = str(input_path.with_suffix(default_ext))

    Path(output).write_text(content, encoding="utf-8")
    err.print(f"[green]Wrote {fmt} to {output}[/green]")
