"""Pydantic data models for structured meeting notes."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MeetingType(str, Enum):
    REGULAR = "regular"
    AD_HOC = "ad_hoc"
    REVIEW = "review"
    DECISION = "decision"
    INFORMATIONAL = "informational"


class ParticipantRole(str, Enum):
    ORGANIZER = "organizer"
    DECISION_MAKER = "decision_maker"
    PROPOSER = "proposer"
    REPORTER = "reporter"
    OBSERVER = "observer"


class DynamicsRelation(str, Enum):
    PROPOSAL_APPROVAL = "proposal_approval"
    OBJECTION_REPROPOSAL = "objection_reproposal"
    DELEGATION = "delegation"
    QUESTION_ANSWER = "question_answer"
    REPORT = "report"
    INSTRUCTION = "instruction"


class AgendaStatus(str, Enum):
    DECIDED = "decided"
    PENDING = "pending"
    REJECTED = "rejected"
    INFORMATIONAL = "informational"


class Participant(BaseModel):
    name: str
    role: ParticipantRole | None = None
    affiliation: str = ""


class ParticipantDynamics(BaseModel):
    from_name: str = Field(alias="from")
    to_name: str = Field(alias="to")
    relation: DynamicsRelation
    topic: str = ""
    detail: str = ""

    model_config = {"populate_by_name": True}


class Alternative(BaseModel):
    option: str
    rejected_because: str


class Decision(BaseModel):
    what: str
    why: str
    alternatives_considered: list[Alternative] = Field(default_factory=list)
    decided_by: list[str] = Field(default_factory=list)


class ActionItem(BaseModel):
    owner: str
    task: str
    due: str = ""
    context: str = ""


class UnresolvedItem(BaseModel):
    issue: str
    blocker: str = ""
    carry_forward_to: str = ""


class AgendaItem(BaseModel):
    title: str
    status: AgendaStatus
    summary: str = ""
    speakers: list[str] = Field(default_factory=list)
    discussion_points: list[str] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    unresolved: list[UnresolvedItem] = Field(default_factory=list)


class MeetingMetadata(BaseModel):
    source_audio: str = ""
    source_transcript: str = ""
    generated_by: str = ""
    generated_at: datetime | None = None
    model: str = ""


class MeetingNote(BaseModel):
    """Root model for a structured meeting note."""

    meeting_id: str
    title: str
    date: datetime
    duration_seconds: int = 0
    meeting_type: MeetingType | None = None
    context: str = ""
    participants: list[Participant] = Field(default_factory=list)
    participant_dynamics: list[ParticipantDynamics] = Field(default_factory=list)
    agenda: list[AgendaItem] = Field(default_factory=list)
    key_takeaways: list[str] = Field(default_factory=list)
    metadata: MeetingMetadata = Field(default_factory=MeetingMetadata)
