"""Shared test fixtures for meeting-note."""

import pytest

from meeting_note.models import (
    ActionItem,
    AgendaItem,
    AgendaStatus,
    Decision,
    MeetingMetadata,
    MeetingNote,
    MeetingType,
    Participant,
    ParticipantDynamics,
    ParticipantRole,
    Utterance,
)


@pytest.fixture
def sample_meeting_note() -> MeetingNote:
    """Return a sample MeetingNote for testing."""
    return MeetingNote(
        meeting_id="test-meeting-001",
        title="Sprint Planning Meeting",
        date="2026-04-07T10:00:00+09:00",
        duration_seconds=3600,
        meeting_type=MeetingType.REGULAR,
        context="Q2 Sprint 3 planning for Project Alpha",
        participants=[
            Participant(name="Tanaka", role=ParticipantRole.ORGANIZER, affiliation="Engineering"),
            Participant(name="Sato", role=ParticipantRole.DECISION_MAKER, affiliation="Product"),
            Participant(name="Suzuki", role=ParticipantRole.PROPOSER, affiliation="Engineering"),
        ],
        participant_dynamics=[
            ParticipantDynamics(
                **{
                    "from": "Suzuki",
                    "to": "Sato",
                    "relation": "proposal_approval",
                    "topic": "API redesign approach",
                    "detail": "Suzuki proposed Option B (incremental migration), Sato approved",
                }
            ),
        ],
        agenda=[
            AgendaItem(
                title="API redesign approach",
                status=AgendaStatus.DECIDED,
                summary="Decided on incremental migration strategy",
                speakers=["Suzuki", "Sato"],
                utterances=[
                    Utterance(speaker="Suzuki", text="I propose we go with incremental migration to avoid a feature freeze."),
                    Utterance(speaker="Sato", text="Agreed. The risk profile is much better with incremental."),
                ],
                discussion_points=[
                    "Current API has performance bottlenecks",
                    "Two approaches: full rewrite vs incremental migration",
                ],
                decisions=[
                    Decision(
                        what="Adopt incremental migration for API redesign",
                        why="Lower risk and allows continuous delivery during migration",
                        alternatives_considered=[
                            {
                                "option": "Full rewrite",
                                "rejected_because": "3-month feature freeze unacceptable for business",
                            }
                        ],
                        decided_by=["Sato", "Suzuki"],
                    ),
                ],
                action_items=[
                    ActionItem(
                        owner="Suzuki",
                        task="Draft migration plan document",
                        due="2026-04-14",
                        context="API redesign decision",
                    ),
                ],
                unresolved=[],
            ),
            AgendaItem(
                title="Testing infrastructure budget",
                status=AgendaStatus.PENDING,
                summary="Need cost estimate before decision",
                speakers=["Tanaka"],
                discussion_points=["Current CI takes 45 minutes", "Proposal to add parallel runners"],
                decisions=[],
                action_items=[
                    ActionItem(
                        owner="Tanaka",
                        task="Prepare cost comparison for CI options",
                        due="2026-04-10",
                    ),
                ],
                unresolved=[
                    {
                        "issue": "Budget approval needed from finance",
                        "blocker": "Q2 budget not yet finalized",
                        "carry_forward_to": "Next sprint planning",
                    }
                ],
            ),
        ],
        key_takeaways=[
            "API redesign will proceed with incremental migration",
            "CI budget decision deferred pending finance approval",
        ],
        raw_transcript="Suzuki: I propose we go with incremental migration.\nSato: Agreed.\nTanaka: Let's discuss CI budget next.",
        metadata=MeetingMetadata(
            source_audio="sprint-planning-2026-04-07.mp3",
            source_transcript="sprint-planning-2026-04-07.txt",
            generated_by="meeting-note v0.1.0",
            generated_at="2026-04-07T12:00:00+09:00",
            model="gemini-2.5-flash",
        ),
    )
