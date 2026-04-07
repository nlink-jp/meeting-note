"""HTML renderer for structured meeting notes."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from meeting_note.compile.labels import (
    DYNAMICS_RELATION_LABELS,
    MEETING_TYPE_LABELS,
    PARTICIPANT_ROLE_LABELS,
    STATUS_LABELS,
)
from meeting_note.models import AgendaStatus, MeetingNote

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_html(note: MeetingNote, *, lang: str = "ja") -> str:
    """Render a MeetingNote as self-contained HTML."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
    )
    env.filters["duration_min"] = lambda secs: secs // 60 if secs else 0
    env.filters["format_date"] = lambda dt: dt.strftime("%Y-%m-%d %H:%M") if dt else ""
    env.filters["role_label"] = lambda v: PARTICIPANT_ROLE_LABELS.get(v, v) if v else ""
    env.filters["relation_label"] = lambda v: DYNAMICS_RELATION_LABELS.get(v, v) if v else ""
    env.filters["meeting_type_label"] = lambda v: MEETING_TYPE_LABELS.get(v, v) if v else ""
    env.filters["status_label"] = lambda s: STATUS_LABELS.get(s, str(s)) if s else ""
    env.filters["status_css"] = _status_css

    template = env.get_template("report.html")

    generated_at = ""
    if note.metadata.generated_at:
        generated_at = note.metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")

    return template.render(
        note=note,
        lang=lang,
        generated_at=generated_at,
    )


def _status_css(status: AgendaStatus) -> str:
    """Return CSS class suffix for a status."""
    return status.value if isinstance(status, AgendaStatus) else str(status)
