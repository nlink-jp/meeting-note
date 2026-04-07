"""Tests for HTML renderer."""

from meeting_note.compile.html import render_html
from meeting_note.models import MeetingNote


class TestRenderHtml:
    def test_valid_html_structure(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html

    def test_contains_title(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "Sprint Planning Meeting" in html

    def test_self_contained(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "<style>" in html
        assert 'rel="stylesheet"' not in html
        assert "<script src=" not in html

    def test_contains_participants(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "Tanaka" in html
        assert "Sato" in html
        assert "Suzuki" in html

    def test_contains_status_badges(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "badge-decided" in html
        assert "badge-pending" in html

    def test_contains_decisions_with_why(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "why-box" in html
        assert "Lower risk" in html

    def test_contains_action_items(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "Draft migration plan" in html
        assert "2026-04-14" in html

    def test_contains_unresolved(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "Budget approval" in html

    def test_contains_key_takeaways(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "incremental migration" in html

    def test_minimal_meeting(self) -> None:
        note = MeetingNote(title="Minimal", date="2026-04-07T10:00:00+09:00")
        html = render_html(note)
        assert "<!DOCTYPE html>" in html
        assert "Minimal" in html

    def test_lang_attribute(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note, lang="en")
        assert 'lang="en"' in html

    def test_localized_labels(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "参加者" in html
        assert "議題" in html
        assert "主要な結論" in html
        assert "決定事項" in html

    def test_role_labels_localized(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "主催者" in html

    def test_relation_labels_localized(self, sample_meeting_note: MeetingNote) -> None:
        html = render_html(sample_meeting_note)
        assert "提案" in html
