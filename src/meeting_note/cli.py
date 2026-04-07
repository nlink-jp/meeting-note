"""CLI entry point for meeting-note."""

import click

from meeting_note import __version__


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
def ingest(audio: str | None, transcript: str | None, output: str, project: str, location: str, model: str) -> None:
    """Extract structured meeting data from audio and/or transcript."""
    if not audio and not transcript:
        raise click.UsageError("At least one of --audio or --transcript is required.")
    click.echo("ingest: not yet implemented")


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--format", "-f", "fmt", type=click.Choice(["markdown", "html"]), default="markdown", help="Output format")
@click.option("--output", "-o", default="", help="Output file path")
def compile(input_file: str, fmt: str, output: str) -> None:
    """Compile structured JSON into Markdown or HTML."""
    click.echo("compile: not yet implemented")
