from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from support_ai.domain.enums import (
    AnswerSource,
    AnswerStatus,
    Channel,
    ClientPlatform,
    DecisionReason,
    HandlingRoute,
    LanguageCode,
    RiskLevel,
    TicketCategory,
    TicketStatus,
)


class TicketMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thread_id: str | None = Field(default=None, max_length=255)
    language: LanguageCode = LanguageCode.UNKNOWN
    client: ClientPlatform = ClientPlatform.UNKNOWN
    app_version: str | None = Field(default=None, max_length=64)


class CreateTicketRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: str | None = Field(default=None, max_length=255)
    channel: Channel
    text: str = Field(min_length=1, max_length=10_000)
    user_id: str | None = Field(default=None, max_length=255)
    metadata: TicketMetadata = Field(default_factory=TicketMetadata)


class CreateTicketResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticket_id: UUID
    external_id: str | None
    status: TicketStatus
    route: HandlingRoute
    category: TicketCategory
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    reason: DecisionReason


class TicketAnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_id: UUID
    text: str
    source: AnswerSource
    status: AnswerStatus
    model_name: str | None
    model_version: str | None


class RetrievalResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retrieval_run_id: UUID
    document_id: str
    rank: int
    score: float = Field(ge=0.0, le=1.0)
    retriever_name: str
    retriever_version: str


class TicketDetailsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticket_id: UUID
    external_id: str | None
    status: TicketStatus
    route: HandlingRoute | None
    category: TicketCategory | None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    risk_level: RiskLevel | None
    contains_pii: bool
    reason: DecisionReason | None
    retrieval_results: list[RetrievalResultResponse]
    answer: TicketAnswerResponse | None


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str


class ReadyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    generation_status: str
    queue_backend: str
    llm_backend: str
    generator_name: str
    generator_version: str
    llm_available: bool
    llm_error: str | None


class MetricsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timings: dict[str, dict[str, float | int]]
    counters: dict[str, int]
