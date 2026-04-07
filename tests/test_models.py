"""Tests for meeting-note data models."""

import json

from meeting_note.models import (
    AgendaItem,
    AgendaStatus,
    MeetingNote,
    MeetingType,
    Participant,
    ParticipantRole,
)


class TestMeetingNote:
    """Tests for the MeetingNote root model."""

    def test_minimal_meeting(self) -> None:
        """MeetingNote can be created with only required fields."""
        note = MeetingNote(
            meeting_id="test-001",
            title="Test Meeting",
            date="2026-04-07T10:00:00+09:00",
        )
        assert note.meeting_id == "test-001"
        assert note.title == "Test Meeting"
        assert note.participants == []
        assert note.agenda == []

    def test_full_meeting(self, sample_meeting_note: MeetingNote) -> None:
        """MeetingNote with all fields populates correctly."""
        note = sample_meeting_note
        assert note.meeting_type == MeetingType.REGULAR
        assert len(note.participants) == 3
        assert len(note.agenda) == 2
        assert len(note.participant_dynamics) == 1
        assert len(note.key_takeaways) == 2

    def test_json_roundtrip(self, sample_meeting_note: MeetingNote) -> None:
        """MeetingNote serializes to JSON and back without data loss."""
        json_str = sample_meeting_note.model_dump_json(by_alias=True)
        parsed = json.loads(json_str)
        restored = MeetingNote.model_validate(parsed)
        assert restored.meeting_id == sample_meeting_note.meeting_id
        assert len(restored.agenda) == len(sample_meeting_note.agenda)
        assert restored.agenda[0].decisions[0].why == sample_meeting_note.agenda[0].decisions[0].why


class TestParticipant:
    def test_minimal(self) -> None:
        p = Participant(name="Test")
        assert p.name == "Test"
        assert p.role is None

    def test_with_role(self) -> None:
        p = Participant(name="Test", role=ParticipantRole.ORGANIZER)
        assert p.role == ParticipantRole.ORGANIZER


class TestAgendaItem:
    def test_decided_item(self, sample_meeting_note: MeetingNote) -> None:
        item = sample_meeting_note.agenda[0]
        assert item.status == AgendaStatus.DECIDED
        assert len(item.decisions) == 1
        assert item.decisions[0].why != ""
        assert len(item.decisions[0].alternatives_considered) == 1

    def test_pending_item(self, sample_meeting_note: MeetingNote) -> None:
        item = sample_meeting_note.agenda[1]
        assert item.status == AgendaStatus.PENDING
        assert len(item.decisions) == 0
        assert len(item.unresolved) == 1
        assert item.unresolved[0].blocker != ""
