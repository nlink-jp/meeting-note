"""Markdown renderer for structured meeting notes."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from meeting_note.compile.labels import (
    DYNAMICS_RELATION_LABELS,
    MEETING_TYPE_LABELS,
    PARTICIPANT_ROLE_LABELS,
    STATUS_LABELS,
)
from meeting_note.models import AgendaStatus, MeetingNote


def render_markdown(note: MeetingNote, *, tz: str = "Asia/Tokyo") -> str:
    """Render a MeetingNote as Markdown."""
    zi = ZoneInfo(tz)
    lines: list[str] = []

    # Header
    lines.append(f"# {note.title}")
    lines.append("")

    # Metadata
    lines.append(f"- **日時**: {note.date.strftime('%Y-%m-%d %H:%M')}")
    if note.duration_seconds:
        minutes = note.duration_seconds // 60
        lines.append(f"- **所要時間**: {minutes}分")
    if note.meeting_type:
        lines.append(f"- **種別**: {MEETING_TYPE_LABELS.get(note.meeting_type.value, note.meeting_type.value)}")
    if note.context:
        lines.append(f"- **背景**: {note.context}")
    lines.append("")

    # Participants
    if note.participants:
        lines.append("## 参加者")
        lines.append("")
        lines.append("| 氏名 | 役割 | 所属 |")
        lines.append("|------|------|------|")
        for p in note.participants:
            role = PARTICIPANT_ROLE_LABELS.get(p.role.value, p.role.value) if p.role else ""
            lines.append(f"| {_escape_cell(p.name)} | {_escape_cell(role)} | {_escape_cell(p.affiliation)} |")
        lines.append("")

    # Participant dynamics
    if note.participant_dynamics:
        lines.append("## 参加者間の関係性")
        lines.append("")
        lines.append("| 発信者 | 受信者 | 関係 | 議題 | 詳細 |")
        lines.append("|--------|--------|------|------|------|")
        for d in note.participant_dynamics:
            relation = DYNAMICS_RELATION_LABELS.get(d.relation.value, d.relation.value)
            lines.append(
                f"| {_escape_cell(d.from_name)} | {_escape_cell(d.to_name)} "
                f"| {_escape_cell(relation)} | {_escape_cell(d.topic)} "
                f"| {_escape_cell(d.detail)} |"
            )
        lines.append("")

    # Agenda
    if note.agenda:
        lines.append("## 議題")
        lines.append("")
        for i, item in enumerate(note.agenda, 1):
            status_label = _status_label(item.status)
            lines.append(f"### {i}. {item.title} {status_label}")
            lines.append("")

            if item.summary:
                lines.append(f"**概要**: {item.summary}")
                lines.append("")

            if item.speakers:
                lines.append(f"**発言者**: {', '.join(item.speakers)}")
                lines.append("")

            # Discussion points
            if item.discussion_points:
                lines.append("#### 議論のポイント")
                lines.append("")
                for point in item.discussion_points:
                    lines.append(f"- {point}")
                lines.append("")

            # Decisions
            if item.decisions:
                lines.append("#### 決定事項")
                lines.append("")
                for decision in item.decisions:
                    lines.append(f"**決定**: {decision.what}")
                    lines.append("")
                    if decision.why:
                        lines.append(f"> **理由**: {decision.why}")
                        lines.append("")
                    if decision.alternatives_considered:
                        lines.append("**検討された代替案**:")
                        lines.append("")
                        for alt in decision.alternatives_considered:
                            lines.append(f"- ~~{alt.option}~~ -- {alt.rejected_because}")
                        lines.append("")
                    if decision.decided_by:
                        lines.append(f"**決定者**: {', '.join(decision.decided_by)}")
                        lines.append("")

            # Action items
            if item.action_items:
                lines.append("#### アクションアイテム")
                lines.append("")
                lines.append("| 担当者 | タスク | 期限 | 背景 |")
                lines.append("|--------|--------|------|------|")
                for ai in item.action_items:
                    lines.append(
                        f"| {_escape_cell(ai.owner)} | {_escape_cell(ai.task)} "
                        f"| {_escape_cell(ai.due)} | {_escape_cell(ai.context)} |"
                    )
                lines.append("")

            # Unresolved
            if item.unresolved:
                lines.append("#### 未解決事項")
                lines.append("")
                lines.append("| 課題 | ブロッカー | 持ち越し先 |")
                lines.append("|------|-----------|-----------|")
                for u in item.unresolved:
                    lines.append(
                        f"| {_escape_cell(u.issue)} | {_escape_cell(u.blocker)} "
                        f"| {_escape_cell(u.carry_forward_to)} |"
                    )
                lines.append("")

    # Key takeaways
    if note.key_takeaways:
        lines.append("## 主要な結論")
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
            local_dt = note.metadata.generated_at.astimezone(zi)
            generated_at = f" ({local_dt.strftime('%Y-%m-%d %H:%M:%S')})"
        lines.append(f"*{note.metadata.generated_by} により自動生成{generated_at}*")
        lines.append("")

    return "\n".join(lines)


def _escape_cell(text: str) -> str:
    """Escape pipe and newline characters for Markdown table cells."""
    return text.replace("|", "\\|").replace("\n", "<br>")


def _status_label(status: AgendaStatus) -> str:
    """Return a localized status label string."""
    return STATUS_LABELS.get(status, "")
