from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from support_ai.adapters.in_memory import (
    InMemoryAnswerRepository,
    InMemoryDecisionRepository,
    InMemoryTicketRepository,
)
from support_ai.adapters.llm import (
    UnavailableAnswerGenerator,
    build_answer_generator,
)
from support_ai.adapters.ml import (
    RegexPiiDetector,
    RuleBasedTicketClassifier,
)
from support_ai.adapters.observability import InMemoryMetricsRecorder
from support_ai.adapters.retrieval import TfidfKnowledgeBaseRetriever
from support_ai.adapters.safety import DeterministicSafetyChecker
from support_ai.application.ports.repositories import (
    AnswerRepository,
    DecisionRepository,
    TicketRepository,
)
from support_ai.application.ports.services import (
    GenerationQueue,
    PiiDetector,
    TicketClassifier,
)
from support_ai.application.use_cases.generate_answer import (
    GenerateAnswerUseCase,
    LLMUnavailableError,
)
from support_ai.application.use_cases.get_ticket_details import (
    GetTicketDetailsUseCase,
)
from support_ai.application.use_cases.process_ticket import ProcessTicketUseCase
from support_ai.domain.policies import RiskPolicy
from support_ai.infrastructure.queue_factory import build_generation_queue


def default_knowledge_base_path() -> Path:
    return Path(__file__).resolve().parents[4] / "data" / "knowledge_base.json"


class AppContainer:
    def __init__(self) -> None:
        self.ticket_repository: TicketRepository = InMemoryTicketRepository()
        self.decision_repository: DecisionRepository = InMemoryDecisionRepository()
        self.answer_repository: AnswerRepository = InMemoryAnswerRepository()
        self.metrics = InMemoryMetricsRecorder()

        self.classifier: TicketClassifier = RuleBasedTicketClassifier()
        self.pii_detector: PiiDetector = RegexPiiDetector()
        self.risk_policy = RiskPolicy()

        self.retriever = TfidfKnowledgeBaseRetriever.from_json(
            default_knowledge_base_path()
        )

        self.llm_backend = os.getenv("LLM_BACKEND", "mock")
        self.llm_available = True
        self.llm_error: str | None = None

        try:
            self.generator = build_answer_generator()
        except LLMUnavailableError as exc:
            self.llm_available = False
            self.llm_error = str(exc)
            self.generator = UnavailableAnswerGenerator(
                reason=str(exc),
                requested_model=os.getenv("QWEN_MODEL_ID"),
            )

        self.safety_checker = DeterministicSafetyChecker()

        self.generate_answer_use_case = GenerateAnswerUseCase(
            ticket_repository=self.ticket_repository,
            decision_repository=self.decision_repository,
            answer_repository=self.answer_repository,
            retriever=self.retriever,
            generator=self.generator,
            safety_checker=self.safety_checker,
            retrieval_score_threshold=0.15,
            metrics=self.metrics,
        )

        self.queue_backend = os.getenv("QUEUE_BACKEND", "local")
        self.generation_queue: GenerationQueue = self._build_queue(
            self.queue_backend
        )

        self.process_ticket_use_case = ProcessTicketUseCase(
            classifier=self.classifier,
            pii_detector=self.pii_detector,
            risk_policy=self.risk_policy,
            ticket_repository=self.ticket_repository,
            decision_repository=self.decision_repository,
            generation_queue=self.generation_queue,
            metrics=self.metrics,
        )

        self.get_ticket_details_use_case = GetTicketDetailsUseCase(
            ticket_repository=self.ticket_repository,
            decision_repository=self.decision_repository,
            answer_repository=self.answer_repository,
        )

    @property
    def generation_status(self) -> str:
        return "ready" if self.llm_available else "degraded"

    def close(self) -> None:
        close = getattr(self.generation_queue, "close", None)
        if callable(close):
            close()

    def _build_queue(self, backend: str) -> GenerationQueue:
        if backend == "celery":
            from support_ai.infrastructure.celery_app import celery_app

            return build_generation_queue(
                "celery",
                celery_client=celery_app,
                metrics=self.metrics,
            )

        if backend == "memory":
            return build_generation_queue(
                "memory",
                metrics=self.metrics,
            )

        if backend == "local":
            return build_generation_queue(
                "local",
                handler=self.generate_answer_use_case.execute,
                metrics=self.metrics,
            )

        raise ValueError(f"Unsupported QUEUE_BACKEND: {backend}")


@lru_cache
def get_container() -> AppContainer:
    return AppContainer()


def reset_container() -> None:
    if get_container.cache_info().currsize:
        get_container().close()
    get_container.cache_clear()


def get_process_ticket_use_case() -> ProcessTicketUseCase:
    return get_container().process_ticket_use_case


def get_ticket_details_use_case() -> GetTicketDetailsUseCase:
    return get_container().get_ticket_details_use_case
