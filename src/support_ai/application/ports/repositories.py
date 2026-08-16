from typing import Protocol
from uuid import UUID

from support_ai.domain.entities import Answer, Decision, Ticket


class TicketRepository(Protocol):
    def add(self, ticket: Ticket) -> None:
        ...

    def get(self, ticket_id: UUID) -> Ticket:
        ...

    def save(self, ticket: Ticket) -> None:
        ...


class DecisionRepository(Protocol):
    def add(self, decision: Decision) -> None:
        ...


class AnswerRepository(Protocol):
    def add(self, answer: Answer) -> None:
        ...
