from typing import runtime_checkable

from support_ai.adapters.in_memory import (
    InMemoryAnswerRepository,
    InMemoryDecisionRepository,
    InMemoryTicketRepository,
)
from support_ai.application.ports.repositories import (
    AnswerRepository,
    DecisionRepository,
    TicketRepository,
)


def test_in_memory_ticket_repository_implements_ticket_repository_contract():
    repository: TicketRepository = InMemoryTicketRepository()
    assert repository is not None


def test_in_memory_decision_repository_implements_decision_repository_contract():
    repository: DecisionRepository = InMemoryDecisionRepository()
    assert repository is not None


def test_in_memory_answer_repository_implements_answer_repository_contract():
    repository: AnswerRepository = InMemoryAnswerRepository()
    assert repository is not None
