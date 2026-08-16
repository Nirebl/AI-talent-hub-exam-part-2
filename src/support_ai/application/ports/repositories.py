from typing import Protocol, Sequence
from uuid import UUID

from support_ai.domain.entities import (
    Answer,
    Decision,
    RetrievalResult,
    Ticket,
)


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

    def latest_for_ticket(self, ticket_id: UUID) -> Decision | None:
        ...


class AnswerRepository(Protocol):
    def add(self, answer: Answer) -> None:
        ...

    def latest_for_ticket(self, ticket_id: UUID) -> Answer | None:
        ...


class RetrievalResultRepository(Protocol):
    def add_many(
        self,
        results: Sequence[RetrievalResult],
    ) -> None:
        ...

    def latest_run_for_ticket(
        self,
        ticket_id: UUID,
    ) -> Sequence[RetrievalResult]:
        ...
