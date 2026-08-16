from uuid import UUID

from sqlalchemy.orm import Session

from support_ai.domain.entities import Answer, Decision, Ticket

from .mappers import (
    answer_to_model,
    decision_to_model,
    ticket_to_domain,
    ticket_to_model,
    update_ticket_model,
)
from .sqlalchemy_models import TicketModel


class SqlAlchemyTicketRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, ticket: Ticket) -> None:
        self._session.add(ticket_to_model(ticket))
        self._session.flush()

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
        self._session.flush()


class SqlAlchemyDecisionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, decision: Decision) -> None:
        self._session.add(decision_to_model(decision))
        self._session.flush()


class SqlAlchemyAnswerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, answer: Answer) -> None:
        self._session.add(answer_to_model(answer))
        self._session.flush()
