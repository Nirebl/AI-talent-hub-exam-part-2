from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from support_ai.application.ports.repositories import (
    AnswerRepository,
    DecisionRepository,
    RetrievalResultRepository,
    TicketRepository,
)
from support_ai.domain.entities import (
    Answer,
    Decision,
    RetrievalResult,
    Ticket,
)


class TicketNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class TicketDetails:
    ticket: Ticket
    latest_decision: Decision | None
    latest_answer: Answer | None
    retrieval_results: Sequence[RetrievalResult]


class GetTicketDetailsUseCase:
    def __init__(
        self,
        *,
        ticket_repository: TicketRepository,
        decision_repository: DecisionRepository,
        answer_repository: AnswerRepository,
        retrieval_result_repository: RetrievalResultRepository,
    ) -> None:
        self._ticket_repository = ticket_repository
        self._decision_repository = decision_repository
        self._answer_repository = answer_repository
        self._retrieval_result_repository = retrieval_result_repository

    def execute(self, ticket_id: UUID) -> TicketDetails:
        try:
            ticket = self._ticket_repository.get(ticket_id)
        except KeyError as exc:
            raise TicketNotFoundError(str(ticket_id)) from exc

        return TicketDetails(
            ticket=ticket,
            latest_decision=self._decision_repository.latest_for_ticket(
                ticket_id
            ),
            latest_answer=self._answer_repository.latest_for_ticket(
                ticket_id
            ),
            retrieval_results=(
                self._retrieval_result_repository.latest_run_for_ticket(
                    ticket_id
                )
            ),
        )
