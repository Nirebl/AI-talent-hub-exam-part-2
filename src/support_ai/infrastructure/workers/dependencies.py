from functools import lru_cache
from pathlib import Path

from support_ai.adapters.in_memory import (
    InMemoryAnswerRepository,
    InMemoryDecisionRepository,
    InMemoryTicketRepository,
)
from support_ai.adapters.llm import build_answer_generator
from support_ai.adapters.retrieval import TfidfKnowledgeBaseRetriever
from support_ai.adapters.safety import DeterministicSafetyChecker
from support_ai.application.ports.repositories import (
    AnswerRepository,
    DecisionRepository,
    TicketRepository,
)
from support_ai.application.use_cases.generate_answer import GenerateAnswerUseCase


def default_knowledge_base_path() -> Path:
    return Path(__file__).resolve().parents[4] / "data" / "knowledge_base.json"


class WorkerContainer:
    """Composition root for answer-generation workers.

    Defaults use in-memory persistence, real local TF-IDF retrieval,
    deterministic mock generation and a deterministic safety checker.
    """

    def __init__(
        self,
        *,
        ticket_repository: TicketRepository | None = None,
        decision_repository: DecisionRepository | None = None,
        answer_repository: AnswerRepository | None = None,
        knowledge_base_path: str | Path | None = None,
    ) -> None:
        self.ticket_repository = (
            ticket_repository or InMemoryTicketRepository()
        )
        self.decision_repository = (
            decision_repository or InMemoryDecisionRepository()
        )
        self.answer_repository = (
            answer_repository or InMemoryAnswerRepository()
        )

        self.retriever = TfidfKnowledgeBaseRetriever.from_json(
            knowledge_base_path or default_knowledge_base_path()
        )
        self.generator = build_answer_generator()
        self.safety_checker = DeterministicSafetyChecker()

        self.generate_answer_use_case = GenerateAnswerUseCase(
            ticket_repository=self.ticket_repository,
            decision_repository=self.decision_repository,
            answer_repository=self.answer_repository,
            retriever=self.retriever,
            generator=self.generator,
            safety_checker=self.safety_checker,
            retrieval_score_threshold=0.15,
        )


@lru_cache
def get_worker_container() -> WorkerContainer:
    return WorkerContainer()


def get_generate_answer_use_case() -> GenerateAnswerUseCase:
    return get_worker_container().generate_answer_use_case
