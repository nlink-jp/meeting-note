"""Tests for meeting-note data models."""

import json

from meeting_note.models import (
    ActionItem,
    AgendaItem,
    AgendaStatus,
    Decision,
    MeetingNote,
    MeetingType,
    Participant,
    ParticipantRole,
    UnresolvedItem,
    Utterance,
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


class TestFieldValidators:
    """Tests for LLM output normalization validators."""

    def test_decision_none_to_empty_string(self) -> None:
        d = Decision.model_validate({"what": None, "why": None})
        assert d.what == ""
        assert d.why == ""

    def test_decision_list_to_string(self) -> None:
        d = Decision.model_validate({"what": ["point 1", "point 2"], "why": "reason"})
        assert d.what == "point 1\npoint 2"

    def test_action_item_none_to_empty(self) -> None:
        a = ActionItem.model_validate({"owner": "Tanaka", "task": "Do thing", "due": None, "context": None})
        assert a.due == ""
        assert a.context == ""

    def test_action_item_list_to_string(self) -> None:
        a = ActionItem.model_validate({"owner": "Tanaka", "task": ["step 1", "step 2"]})
        assert a.task == "step 1\nstep 2"

    def test_unresolved_none_to_empty(self) -> None:
        u = UnresolvedItem.model_validate({"issue": "something", "blocker": None})
        assert u.blocker == ""

    def test_meeting_id_auto_generated(self) -> None:
        note = MeetingNote(title="Test", date="2026-04-07T10:00:00+09:00")
        assert note.meeting_id != ""
        assert len(note.meeting_id) == 12

    def test_meeting_id_deterministic(self) -> None:
        note1 = MeetingNote(title="Test", date="2026-04-07T10:00:00+09:00")
        note2 = MeetingNote(title="Test", date="2026-04-07T10:00:00+09:00")
        assert note1.meeting_id == note2.meeting_id

    def test_meeting_id_preserved_if_set(self) -> None:
        note = MeetingNote(meeting_id="custom-id", title="Test", date="2026-04-07T10:00:00+09:00")
        assert note.meeting_id == "custom-id"

    def test_utterance_coerce_none(self) -> None:
        u = Utterance.model_validate({"speaker": "Test", "text": None})
        assert u.text == ""

    def test_utterance_coerce_list(self) -> None:
        u = Utterance.model_validate({"speaker": "Test", "text": ["line1", "line2"]})
        assert u.text == "line1\nline2"


class TestRawTranscript:
    def test_raw_transcript_preserved(self, sample_meeting_note: MeetingNote) -> None:
        assert "Suzuki" in sample_meeting_note.raw_transcript
        assert "incremental migration" in sample_meeting_note.raw_transcript

    def test_utterances_in_agenda(self, sample_meeting_note: MeetingNote) -> None:
        item = sample_meeting_note.agenda[0]
        assert len(item.utterances) == 2
        assert item.utterances[0].speaker == "Suzuki"
        assert "incremental" in item.utterances[0].text

    def test_json_roundtrip_with_utterances(self, sample_meeting_note: MeetingNote) -> None:
        import json
        json_str = sample_meeting_note.model_dump_json(by_alias=True)
        parsed = json.loads(json_str)
        restored = MeetingNote.model_validate(parsed)
        assert restored.raw_transcript == sample_meeting_note.raw_transcript
        assert len(restored.agenda[0].utterances) == 2
