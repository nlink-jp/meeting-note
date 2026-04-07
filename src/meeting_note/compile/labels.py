"""Localized display labels for enum values."""

from meeting_note.models import AgendaStatus

STATUS_LABELS: dict[AgendaStatus, str] = {
    AgendaStatus.DECIDED: "[決定]",
    AgendaStatus.PENDING: "[保留]",
    AgendaStatus.REJECTED: "[却下]",
    AgendaStatus.INFORMATIONAL: "[情報共有]",
}

MEETING_TYPE_LABELS: dict[str, str] = {
    "regular": "定例",
    "ad_hoc": "臨時",
    "review": "レビュー",
    "decision": "意思決定",
    "informational": "情報共有",
}

PARTICIPANT_ROLE_LABELS: dict[str, str] = {
    "organizer": "主催者",
    "decision_maker": "意思決定者",
    "proposer": "提案者",
    "reporter": "報告者",
    "observer": "オブザーバー",
}

DYNAMICS_RELATION_LABELS: dict[str, str] = {
    "proposal_approval": "提案 → 承認",
    "objection_reproposal": "反論 → 再提案",
    "delegation": "委任",
    "question_answer": "質疑応答",
    "report": "報告",
    "instruction": "指示",
}
