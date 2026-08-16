from support_ai.domain.entities import Answer, Decision, RetrievalResult, Ticket
from support_ai.domain.enums import (
    AnswerSource,
    AnswerStatus,
    Channel,
    DecisionReason,
    HandlingRoute,
    RiskLevel,
    TicketCategory,
    TicketStatus,
)

from .sqlalchemy_models import AnswerModel, DecisionModel, RetrievalResultModel, TicketModel


def ticket_to_model(ticket: Ticket) -> TicketModel:
    return TicketModel(
        id=ticket.id,
        external_id=ticket.external_id,
        user_id=ticket.user_id,
        channel=ticket.channel.value,
        text=ticket.text,
        metadata_json=dict(ticket.metadata),
        status=ticket.status.value,
        route=ticket.route.value if ticket.route else None,
        category=ticket.category.value if ticket.category else None,
        category_confidence=ticket.category_confidence,
        risk_level=ticket.risk_level.value if ticket.risk_level else None,
        contains_pii=ticket.contains_pii,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def update_ticket_model(model: TicketModel, ticket: Ticket) -> None:
    model.external_id = ticket.external_id
    model.user_id = ticket.user_id
    model.channel = ticket.channel.value
    model.text = ticket.text
    model.metadata_json = dict(ticket.metadata)
    model.status = ticket.status.value
    model.route = ticket.route.value if ticket.route else None
    model.category = ticket.category.value if ticket.category else None
    model.category_confidence = ticket.category_confidence
    model.risk_level = ticket.risk_level.value if ticket.risk_level else None
    model.contains_pii = ticket.contains_pii
    model.updated_at = ticket.updated_at


def ticket_to_domain(model: TicketModel) -> Ticket:
    return Ticket(
        id=model.id,
        external_id=model.external_id,
        user_id=model.user_id,
        channel=Channel(model.channel),
        text=model.text,
        metadata=dict(model.metadata_json or {}),
        status=TicketStatus(model.status),
        route=HandlingRoute(model.route) if model.route else None,
        category=TicketCategory(model.category) if model.category else None,
        category_confidence=model.category_confidence,
        risk_level=RiskLevel(model.risk_level) if model.risk_level else None,
        contains_pii=model.contains_pii,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def decision_to_model(decision: Decision) -> DecisionModel:
    return DecisionModel(
        id=decision.id,
        ticket_id=decision.ticket_id,
        category=decision.category.value,
        confidence=decision.confidence,
        risk_level=decision.risk_level.value,
        route=decision.route.value,
        reason=decision.reason.value,
        classifier_name=decision.classifier_name,
        classifier_version=decision.classifier_version,
        policy_version=decision.policy_version,
        created_at=decision.created_at,
    )


def decision_to_domain(model: DecisionModel) -> Decision:
    return Decision(
        id=model.id,
        ticket_id=model.ticket_id,
        category=TicketCategory(model.category),
        confidence=model.confidence,
        risk_level=RiskLevel(model.risk_level),
        route=HandlingRoute(model.route),
        reason=DecisionReason(model.reason),
        classifier_name=model.classifier_name,
        classifier_version=model.classifier_version,
        policy_version=model.policy_version,
        created_at=model.created_at,
    )


def answer_to_model(answer: Answer) -> AnswerModel:
    return AnswerModel(
        id=answer.id,
        ticket_id=answer.ticket_id,
        text=answer.text,
        source=answer.source.value,
        status=answer.status.value,
        model_name=answer.model_name,
        model_version=answer.model_version,
        created_at=answer.created_at,
    )


def answer_to_domain(model: AnswerModel) -> Answer:
    return Answer(
        id=model.id,
        ticket_id=model.ticket_id,
        text=model.text,
        source=AnswerSource(model.source),
        status=AnswerStatus(model.status),
        model_name=model.model_name,
        model_version=model.model_version,
        created_at=model.created_at,
    )


def retrieval_result_to_model(
    result: RetrievalResult,
) -> RetrievalResultModel:
    return RetrievalResultModel(
        id=result.id,
        ticket_id=result.ticket_id,
        retrieval_run_id=result.retrieval_run_id,
        document_id=result.document_id,
        rank=result.rank,
        score=result.score,
        retriever_name=result.retriever_name,
        retriever_version=result.retriever_version,
        created_at=result.created_at,
    )


def retrieval_result_to_domain(
    model: RetrievalResultModel,
) -> RetrievalResult:
    return RetrievalResult(
        id=model.id,
        ticket_id=model.ticket_id,
        retrieval_run_id=model.retrieval_run_id,
        document_id=model.document_id,
        rank=model.rank,
        score=model.score,
        retriever_name=model.retriever_name,
        retriever_version=model.retriever_version,
        created_at=model.created_at,
    )
