import os
from functools import lru_cache
from pathlib import Path

from support_ai.adapters.in_memory import InMemoryRetrievalResultRepository
from support_ai.adapters.llm import build_answer_generator
from support_ai.adapters.observability import InMemoryMetricsRecorder
from support_ai.adapters.retrieval import TfidfKnowledgeBaseRetriever
from support_ai.adapters.safety import DeterministicSafetyChecker
from support_ai.application.ports.repositories import (
    AnswerRepository,
    DecisionRepository,
    RetrievalResultRepository,
    TicketRepository,
)
from support_ai.application.use_cases.generate_answer import GenerateAnswerUseCase
from support_ai.infrastructure.persistence_factory import build_repositories
from support_ai.infrastructure.paths import resolve_knowledge_base_path




class WorkerContainer:
    def __init__(
        self,
        *,
        ticket_repository: TicketRepository | None = None,
        decision_repository: DecisionRepository | None = None,
        answer_repository: AnswerRepository | None = None,
        retrieval_result_repository: RetrievalResultRepository | None = None,
        knowledge_base_path: str | Path | None = None,
    ) -> None:
        self.repositories = None

        if all(
            repository is None
            for repository in (
                ticket_repository,
                decision_repository,
                answer_repository,
                retrieval_result_repository,
            )
        ):
            self.repositories = build_repositories(
                os.getenv("PERSISTENCE_BACKEND", "memory"),
                database_url=os.getenv(
                    "DATABASE_URL",
                    "sqlite:///./support_ai.db",
                ),
            )
            ticket_repository = self.repositories.tickets
            decision_repository = self.repositories.decisions
            answer_repository = self.repositories.answers
            retrieval_result_repository = (
                self.repositories.retrieval_results
            )

        supplied_core = (
            ticket_repository is not None
            and decision_repository is not None
            and answer_repository is not None
        )

        if supplied_core and retrieval_result_repository is None:
            retrieval_result_repository = (
                InMemoryRetrievalResultRepository()
            )

        if any(
            repository is None
            for repository in (
                ticket_repository,
                decision_repository,
                answer_repository,
                retrieval_result_repository,
            )
        ):
            raise ValueError(
                "ticket, decision and answer repositories "
                "must be supplied together"
            )

        self.ticket_repository = ticket_repository
        self.decision_repository = decision_repository
        self.answer_repository = answer_repository
        self.retrieval_result_repository = retrieval_result_repository
        self.metrics = InMemoryMetricsRecorder()

        self.retriever = TfidfKnowledgeBaseRetriever.from_json(
            resolve_knowledge_base_path(knowledge_base_path)
        )
        self.generator = build_answer_generator()
        self.safety_checker = DeterministicSafetyChecker()

        self.generate_answer_use_case = GenerateAnswerUseCase(
            ticket_repository=self.ticket_repository,
            decision_repository=self.decision_repository,
            answer_repository=self.answer_repository,
            retrieval_result_repository=self.retrieval_result_repository,
            retriever=self.retriever,
            generator=self.generator,
            safety_checker=self.safety_checker,
            retrieval_score_threshold=0.15,
            metrics=self.metrics,
        )

    def close(self) -> None:
        if self.repositories is not None:
            self.repositories.close()


@lru_cache
def get_worker_container() -> WorkerContainer:
    return WorkerContainer()


def get_generate_answer_use_case() -> GenerateAnswerUseCase:
    return get_worker_container().generate_answer_use_case
