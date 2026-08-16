from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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

PersistenceBackend = Literal["memory"]


@dataclass(frozen=True, slots=True)
class RepositoryBundle:
    tickets: TicketRepository
    decisions: DecisionRepository
    answers: AnswerRepository


def build_repositories(
    backend: PersistenceBackend = "memory",
) -> RepositoryBundle:
    if backend == "memory":
        return RepositoryBundle(
            tickets=InMemoryTicketRepository(),
            decisions=InMemoryDecisionRepository(),
            answers=InMemoryAnswerRepository(),
        )

    raise ValueError(f"Unsupported persistence backend: {backend}")
