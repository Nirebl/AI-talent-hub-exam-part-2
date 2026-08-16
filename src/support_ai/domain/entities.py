from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from .enums import (
    AnswerSource,
    AnswerStatus,
    Channel,
    DecisionReason,
    HandlingRoute,
    RiskLevel,
    TicketCategory,
    TicketStatus,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class Prediction:
    category: TicketCategory
    confidence: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(slots=True)
class Ticket:
    text: str
    channel: Channel

    external_id: str | None = None
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    id: UUID = field(default_factory=uuid4)
    status: TicketStatus = TicketStatus.PENDING
    route: HandlingRoute | None = None
    category: TicketCategory | None = None
    category_confidence: float | None = None
    risk_level: RiskLevel | None = None
    contains_pii: bool = False
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.text = self.text.strip()
        if not self.text:
            raise ValueError("ticket text must not be empty")

    @property
    def classifier_text(self) -> str:
        return self.text

    def apply_routing(
        self,
        *,
        prediction: Prediction,
        route: HandlingRoute,
        risk_level: RiskLevel,
        contains_pii: bool,
    ) -> None:
        self.category = prediction.category
        self.category_confidence = prediction.confidence
        self.route = route
        self.risk_level = risk_level
        self.contains_pii = contains_pii
        self.updated_at = utc_now()

    def mark_processing(self) -> None:
        self.status = TicketStatus.PROCESSING
        self.updated_at = utc_now()

    def mark_resolved(self) -> None:
        self.status = TicketStatus.RESOLVED
        self.updated_at = utc_now()

    def escalate_to_human(self) -> None:
        self.route = HandlingRoute.HUMAN
        self.status = TicketStatus.PENDING
        self.updated_at = utc_now()


@dataclass(frozen=True, slots=True)
class Decision:
    ticket_id: UUID
    category: TicketCategory
    confidence: float
    risk_level: RiskLevel
    route: HandlingRoute
    reason: DecisionReason
    classifier_name: str
    classifier_version: str
    policy_version: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class Answer:
    ticket_id: UUID
    text: str
    source: AnswerSource
    status: AnswerStatus = AnswerStatus.DRAFT
    model_name: str | None = None
    model_version: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
