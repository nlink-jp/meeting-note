"""Tests for Markdown renderer."""

from meeting_note.compile.markdown import _escape_cell, _status_label, render_markdown
from meeting_note.models import AgendaStatus, MeetingNote


class TestRenderMarkdown:
    def test_minimal_meeting(self) -> None:
        note = MeetingNote(title="Minimal Meeting", date="2026-04-07T10:00:00+09:00")
        md = render_markdown(note)
        assert "# Minimal Meeting" in md
        assert "2026-04-07" in md

    def test_full_meeting(self, sample_meeting_note: MeetingNote) -> None:
        md = render_markdown(sample_meeting_note)
        assert "# Sprint Planning Meeting" in md
        assert "## 参加者" in md
        assert "Tanaka" in md
        assert "## 参加者間の関係性" in md
        assert "## 議題" in md
        assert "## 主要な結論" in md

    def test_decided_agenda_has_decisions(self, sample_meeting_note: MeetingNote) -> None:
        md = render_markdown(sample_meeting_note)
        assert "#### 決定事項" in md
        assert "**理由**:" in md
        assert "検討された代替案" in md
        assert "~~Full rewrite~~" in md
        assert "決定者" in md

    def test_pending_agenda_has_unresolved(self, sample_meeting_note: MeetingNote) -> None:
        md = render_markdown(sample_meeting_note)
        assert "#### 未解決事項" in md
        assert "Budget approval" in md
        assert "[保留]" in md

    def test_action_items_table(self, sample_meeting_note: MeetingNote) -> None:
        md = render_markdown(sample_meeting_note)
        assert "#### アクションアイテム" in md
        assert "| 担当者 | タスク | 期限 | 背景 |" in md
        assert "Suzuki" in md
        assert "2026-04-14" in md

    def test_participant_dynamics_table(self, sample_meeting_note: MeetingNote) -> None:
        md = render_markdown(sample_meeting_note)
        assert "| 発信者 | 受信者 | 関係 | 議題 | 詳細 |" in md
        assert "提案 → 承認" in md

    def test_key_takeaways_rendered(self, sample_meeting_note: MeetingNote) -> None:
        md = render_markdown(sample_meeting_note)
        assert "- API redesign will proceed" in md

    def test_duration_rendered(self, sample_meeting_note: MeetingNote) -> None:
        md = render_markdown(sample_meeting_note)
        assert "60分" in md

    def test_metadata_footer(self, sample_meeting_note: MeetingNote) -> None:
        md = render_markdown(sample_meeting_note)
        assert "自動生成" in md

    def test_role_labels_localized(self, sample_meeting_note: MeetingNote) -> None:
        md = render_markdown(sample_meeting_note)
        assert "主催者" in md
        assert "意思決定者" in md
        assert "提案者" in md

    def test_meeting_type_localized(self, sample_meeting_note: MeetingNote) -> None:
        md = render_markdown(sample_meeting_note)
        assert "定例" in md


class TestEscapeCell:
    def test_pipe_escaped(self) -> None:
        assert _escape_cell("a | b") == "a \\| b"

    def test_newline_escaped(self) -> None:
        assert _escape_cell("line1\nline2") == "line1<br>line2"


class TestStatusLabel:
    def test_decided(self) -> None:
        assert _status_label(AgendaStatus.DECIDED) == "[決定]"

    def test_pending(self) -> None:
        assert _status_label(AgendaStatus.PENDING) == "[保留]"

    def test_rejected(self) -> None:
        assert _status_label(AgendaStatus.REJECTED) == "[却下]"

    def test_informational(self) -> None:
        assert _status_label(AgendaStatus.INFORMATIONAL) == "[情報共有]"
