from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from support_ai.domain.enums import (
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


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
