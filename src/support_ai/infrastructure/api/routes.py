from fastapi import APIRouter, Depends, status

from support_ai.application.use_cases.process_ticket import ProcessTicketUseCase
from support_ai.infrastructure.api.dependencies import get_process_ticket_use_case
from support_ai.infrastructure.api.schemas import (
    CreateTicketRequest,
    CreateTicketResponse,
    HealthResponse,
)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health check",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post(
    "/tickets",
    response_model=CreateTicketResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["tickets"],
    summary="Create and route a support ticket",
    description=(
        "Accepts a canonical support ticket. "
        "Closed-set fields are validated as enums by FastAPI/Pydantic. "
        "Risk, category and route are derived by the system and cannot be supplied by the client."
    ),
)
def create_ticket(
    request: CreateTicketRequest,
    use_case: ProcessTicketUseCase = Depends(get_process_ticket_use_case),
) -> CreateTicketResponse:
    result = use_case.execute(
        external_id=request.external_id,
        channel=request.channel,
        text=request.text,
        user_id=request.user_id,
        metadata=request.metadata.model_dump(mode="json"),
    )

    ticket = result.ticket
    decision = result.decision

    return CreateTicketResponse(
        ticket_id=ticket.id,
        external_id=ticket.external_id,
        status=ticket.status,
        route=decision.route,
        category=decision.category,
        confidence=decision.confidence,
        risk_level=decision.risk_level,
        reason=decision.reason,
    )
