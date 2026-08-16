from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from support_ai.domain.entities import (
    Answer,
    Decision,
    RetrievalResult,
    Ticket,
)

from .mappers import (
    answer_to_domain,
    answer_to_model,
    decision_to_domain,
    decision_to_model,
    retrieval_result_to_domain,
    retrieval_result_to_model,
    ticket_to_domain,
    ticket_to_model,
    update_ticket_model,
)
from .sqlalchemy_models import (
    AnswerModel,
    DecisionModel,
    RetrievalResultModel,
    TicketModel,
)


class SqlAlchemyTicketRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, ticket: Ticket) -> None:
        self._session.add(ticket_to_model(ticket))
        self._session.commit()

    def get(self, ticket_id: UUID) -> Ticket:
        model = self._session.get(TicketModel, ticket_id)
        if model is None:
            raise KeyError(f"ticket not found: {ticket_id}")
        return ticket_to_domain(model)

    def save(self, ticket: Ticket) -> None:
        model = self._session.get(TicketModel, ticket.id)
        if model is None:
            raise KeyError(f"ticket not found: {ticket.id}")
        update_ticket_model(model, ticket)
        self._session.commit()

    def find_by_external_id(
        self,
        *,
        channel,
        external_id: str,
    ) -> Ticket | None:
        model = self._session.scalar(
            select(TicketModel)
            .where(
                TicketModel.channel == channel.value,
                TicketModel.external_id == external_id,
            )
            .limit(1)
        )
        return ticket_to_domain(model) if model else None


class SqlAlchemyDecisionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, decision: Decision) -> None:
        self._session.add(decision_to_model(decision))
        self._session.commit()

    def latest_for_ticket(self, ticket_id: UUID) -> Decision | None:
        model = self._session.scalar(
            select(DecisionModel)
            .where(DecisionModel.ticket_id == ticket_id)
            .order_by(DecisionModel.created_at.desc())
            .limit(1)
        )
        return decision_to_domain(model) if model else None


class SqlAlchemyAnswerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, answer: Answer) -> None:
        self._session.add(answer_to_model(answer))
        self._session.commit()

    def latest_for_ticket(self, ticket_id: UUID) -> Answer | None:
        model = self._session.scalar(
            select(AnswerModel)
            .where(AnswerModel.ticket_id == ticket_id)
            .order_by(AnswerModel.created_at.desc())
            .limit(1)
        )
        return answer_to_domain(model) if model else None


class SqlAlchemyRetrievalResultRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(
        self,
        results: Sequence[RetrievalResult],
    ) -> None:
        self._session.add_all(
            retrieval_result_to_model(result)
            for result in results
        )
        self._session.commit()

    def latest_run_for_ticket(
        self,
        ticket_id: UUID,
    ) -> Sequence[RetrievalResult]:
        latest = self._session.scalar(
            select(RetrievalResultModel)
            .where(RetrievalResultModel.ticket_id == ticket_id)
            .order_by(RetrievalResultModel.created_at.desc())
            .limit(1)
        )
        if latest is None:
            return []

        models = self._session.scalars(
            select(RetrievalResultModel)
            .where(
                RetrievalResultModel.ticket_id == ticket_id,
                RetrievalResultModel.retrieval_run_id
                == latest.retrieval_run_id,
            )
            .order_by(RetrievalResultModel.rank.asc())
        ).all()

        return [
            retrieval_result_to_domain(model)
            for model in models
        ]
