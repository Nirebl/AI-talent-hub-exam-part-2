from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from support_ai.application.use_cases.get_ticket_details import (
    GetTicketDetailsUseCase,
    TicketNotFoundError,
)
from support_ai.application.use_cases.process_ticket import ProcessTicketUseCase
from support_ai.domain.enums import TicketStatus
from support_ai.infrastructure.api.dependencies import (
    get_container,
    get_process_ticket_use_case,
    get_ticket_details_use_case,
)
from support_ai.infrastructure.api.schemas import (
    CreateTicketRequest,
    CreateTicketResponse,
    HealthResponse,
    MetricsResponse,
    ReadyResponse,
    RetrievalResultResponse,
    TicketAnswerResponse,
    TicketDetailsResponse,
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


@router.get(
    "/ready",
    response_model=ReadyResponse,
    tags=["system"],
    summary="Readiness and generation capability",
)
def ready() -> ReadyResponse:
    container = get_container()

    return ReadyResponse(
        status="ready",
        generation_status=container.generation_status,
        queue_backend=container.queue_backend,
        llm_backend=container.llm_backend,
        generator_name=container.generator.name,
        generator_version=container.generator.version,
        llm_available=container.llm_available,
        llm_error=container.llm_error,
    )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    tags=["system"],
    summary="Local PoC runtime metrics",
)
def metrics() -> MetricsResponse:
    snapshot = get_container().metrics.snapshot()
    return MetricsResponse(**snapshot)


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
        status=TicketStatus.PENDING,
        route=decision.route,
        category=decision.category,
        confidence=decision.confidence,
        risk_level=decision.risk_level,
        reason=decision.reason,
    )


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketDetailsResponse,
    tags=["tickets"],
    summary="Get current ticket processing result",
)
def get_ticket(
    ticket_id: UUID,
    use_case: GetTicketDetailsUseCase = Depends(
        get_ticket_details_use_case
    ),
) -> TicketDetailsResponse:
    try:
        result = use_case.execute(ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ticket not found",
        ) from exc

    ticket = result.ticket
    decision = result.latest_decision
    answer = result.latest_answer

    answer_response = None
    if answer is not None:
        answer_response = TicketAnswerResponse(
            answer_id=answer.id,
            text=answer.text,
            source=answer.source,
            status=answer.status,
            model_name=answer.model_name,
            model_version=answer.model_version,
        )

    retrieval_results = [
        RetrievalResultResponse(
            retrieval_run_id=item.retrieval_run_id,
            document_id=item.document_id,
            rank=item.rank,
            score=item.score,
            retriever_name=item.retriever_name,
            retriever_version=item.retriever_version,
        )
        for item in result.retrieval_results
    ]

    return TicketDetailsResponse(
        ticket_id=ticket.id,
        external_id=ticket.external_id,
        status=ticket.status,
        route=ticket.route,
        category=ticket.category,
        confidence=ticket.category_confidence,
        risk_level=ticket.risk_level,
        contains_pii=ticket.contains_pii,
        reason=decision.reason if decision else None,
        retrieval_results=retrieval_results,
        answer=answer_response,
    )
