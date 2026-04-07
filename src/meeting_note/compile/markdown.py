"""Markdown renderer for structured meeting notes."""

from __future__ import annotations

from meeting_note.models import AgendaStatus, MeetingNote


def render_markdown(note: MeetingNote) -> str:
    """Render a MeetingNote as Markdown."""
    lines: list[str] = []

    # Header
    lines.append(f"# {note.title}")
    lines.append("")

    # Metadata
    lines.append(f"- **Date**: {note.date.strftime('%Y-%m-%d %H:%M')}")
    if note.duration_seconds:
        minutes = note.duration_seconds // 60
        lines.append(f"- **Duration**: {minutes} min")
    if note.meeting_type:
        lines.append(f"- **Type**: {note.meeting_type.value}")
    if note.context:
        lines.append(f"- **Context**: {note.context}")
    lines.append("")

    # Participants
    if note.participants:
        lines.append("## Participants")
        lines.append("")
        lines.append("| Name | Role | Affiliation |")
        lines.append("|------|------|-------------|")
        for p in note.participants:
            role = p.role.value if p.role else ""
            lines.append(f"| {_escape_cell(p.name)} | {_escape_cell(role)} | {_escape_cell(p.affiliation)} |")
        lines.append("")

    # Participant dynamics
    if note.participant_dynamics:
        lines.append("## Participant Dynamics")
        lines.append("")
        lines.append("| From | To | Relation | Topic | Detail |")
        lines.append("|------|----|----------|-------|--------|")
        for d in note.participant_dynamics:
            lines.append(
                f"| {_escape_cell(d.from_name)} | {_escape_cell(d.to_name)} "
                f"| {_escape_cell(d.relation.value)} | {_escape_cell(d.topic)} "
                f"| {_escape_cell(d.detail)} |"
            )
        lines.append("")

    # Agenda
    if note.agenda:
        lines.append("## Agenda")
        lines.append("")
        for i, item in enumerate(note.agenda, 1):
            status_label = _status_label(item.status)
            lines.append(f"### {i}. {item.title} {status_label}")
            lines.append("")

            if item.summary:
                lines.append(f"**Summary**: {item.summary}")
                lines.append("")

            if item.speakers:
                lines.append(f"**Speakers**: {', '.join(item.speakers)}")
                lines.append("")

            # Discussion points
            if item.discussion_points:
                lines.append("#### Discussion Points")
                lines.append("")
                for point in item.discussion_points:
                    lines.append(f"- {point}")
                lines.append("")

            # Decisions
            if item.decisions:
                lines.append("#### Decisions")
                lines.append("")
                for decision in item.decisions:
                    lines.append(f"**Decision**: {decision.what}")
                    lines.append("")
                    if decision.why:
                        lines.append(f"> **Why**: {decision.why}")
                        lines.append("")
                    if decision.alternatives_considered:
                        lines.append("**Alternatives considered**:")
                        lines.append("")
                        for alt in decision.alternatives_considered:
                            lines.append(f"- ~~{alt.option}~~ -- {alt.rejected_because}")
                        lines.append("")
                    if decision.decided_by:
                        lines.append(f"**Decided by**: {', '.join(decision.decided_by)}")
                        lines.append("")

            # Action items
            if item.action_items:
                lines.append("#### Action Items")
                lines.append("")
                lines.append("| Owner | Task | Due | Context |")
                lines.append("|-------|------|-----|---------|")
                for ai in item.action_items:
                    lines.append(
                        f"| {_escape_cell(ai.owner)} | {_escape_cell(ai.task)} "
                        f"| {_escape_cell(ai.due)} | {_escape_cell(ai.context)} |"
                    )
                lines.append("")

            # Unresolved
            if item.unresolved:
                lines.append("#### Unresolved")
                lines.append("")
                lines.append("| Issue | Blocker | Carry Forward |")
                lines.append("|-------|---------|---------------|")
                for u in item.unresolved:
                    lines.append(
                        f"| {_escape_cell(u.issue)} | {_escape_cell(u.blocker)} "
                        f"| {_escape_cell(u.carry_forward_to)} |"
                    )
                lines.append("")

    # Key takeaways
    if note.key_takeaways:
        lines.append("## Key Takeaways")
        lines.append("")
        for takeaway in note.key_takeaways:
            lines.append(f"- {takeaway}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    if note.metadata.generated_by:
        generated_at = ""
        if note.metadata.generated_at:
            generated_at = f" at {note.metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        lines.append(f"*Generated by {note.metadata.generated_by}{generated_at}*")
        lines.append("")

    return "\n".join(lines)


def _escape_cell(text: str) -> str:
    """Escape pipe and newline characters for Markdown table cells."""
    return text.replace("|", "\\|").replace("\n", "<br>")


def _status_label(status: AgendaStatus) -> str:
    """Return a status label string."""
    labels = {
        AgendaStatus.DECIDED: "[DECIDED]",
        AgendaStatus.PENDING: "[PENDING]",
        AgendaStatus.REJECTED: "[REJECTED]",
        AgendaStatus.INFORMATIONAL: "[INFO]",
    }
    return labels.get(status, "")
