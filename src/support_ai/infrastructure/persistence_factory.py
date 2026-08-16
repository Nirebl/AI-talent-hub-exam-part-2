from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import scoped_session

from support_ai.adapters.in_memory import (
    InMemoryAnswerRepository,
    InMemoryDecisionRepository,
    InMemoryRetrievalResultRepository,
    InMemoryTicketRepository,
)
from support_ai.adapters.persistence.repositories import (
    SqlAlchemyAnswerRepository,
    SqlAlchemyDecisionRepository,
    SqlAlchemyRetrievalResultRepository,
    SqlAlchemyTicketRepository,
)
from support_ai.application.ports.repositories import (
    AnswerRepository,
    DecisionRepository,
    RetrievalResultRepository,
    TicketRepository,
)
from support_ai.infrastructure.database import (
    build_engine,
    build_session_factory,
    create_schema,
)

PersistenceBackend = Literal["memory", "sqlalchemy"]


@dataclass(slots=True)
class RepositoryBundle:
    tickets: TicketRepository
    decisions: DecisionRepository
    answers: AnswerRepository
    retrieval_results: RetrievalResultRepository
    session_registry: scoped_session | None = None

    def close(self) -> None:
        if self.session_registry is not None:
            self.session_registry.remove()


def build_repositories(
    backend: PersistenceBackend = "memory",
    *,
    database_url: str | None = None,
) -> RepositoryBundle:
    if backend == "memory":
        return RepositoryBundle(
            tickets=InMemoryTicketRepository(),
            decisions=InMemoryDecisionRepository(),
            answers=InMemoryAnswerRepository(),
            retrieval_results=InMemoryRetrievalResultRepository(),
        )

    if backend == "sqlalchemy":
        if not database_url:
            raise ValueError(
                "database_url is required for sqlalchemy backend"
            )

        engine = build_engine(database_url)
        create_schema(engine)
        registry = scoped_session(build_session_factory(engine))

        return RepositoryBundle(
            tickets=SqlAlchemyTicketRepository(registry),
            decisions=SqlAlchemyDecisionRepository(registry),
            answers=SqlAlchemyAnswerRepository(registry),
            retrieval_results=SqlAlchemyRetrievalResultRepository(
                registry
            ),
            session_registry=registry,
        )

    raise ValueError(f"Unsupported persistence backend: {backend}")
