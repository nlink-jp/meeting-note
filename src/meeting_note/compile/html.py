"""HTML renderer for structured meeting notes."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from meeting_note.models import MeetingNote

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_html(note: MeetingNote, *, lang: str = "ja") -> str:
    """Render a MeetingNote as self-contained HTML."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
    )
    env.filters["duration_min"] = lambda secs: secs // 60 if secs else 0
    env.filters["format_date"] = lambda dt: dt.strftime("%Y-%m-%d %H:%M") if dt else ""

    template = env.get_template("report.html")

    generated_at = ""
    if note.metadata.generated_at:
        generated_at = note.metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")

    return template.render(
        note=note,
        lang=lang,
        generated_at=generated_at,
    )
