from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

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
from support_ai.application.ports.services import GenerationQueue
from support_ai.application.use_cases.generate_answer import (
    GenerateAnswerUseCase,
    LLMUnavailableError,
)
from support_ai.application.use_cases.get_ticket_details import (
    GetTicketDetailsUseCase,
)
from support_ai.application.use_cases.process_ticket import ProcessTicketUseCase
from support_ai.domain.policies import RiskPolicy
from support_ai.infrastructure.persistence_factory import build_repositories
from support_ai.infrastructure.queue_factory import build_generation_queue


def default_knowledge_base_path() -> Path:
    return Path(__file__).resolve().parents[4] / "data" / "knowledge_base.json"


class AppContainer:
    def __init__(self) -> None:
        self.metrics = InMemoryMetricsRecorder()
        self.queue_backend = os.getenv("QUEUE_BACKEND", "local")
        self.persistence_backend = os.getenv(
            "PERSISTENCE_BACKEND",
            "memory",
        )
        self.database_url = os.getenv(
            "DATABASE_URL",
            "sqlite:///./support_ai.db",
        )

        self.repositories = build_repositories(
            self.persistence_backend,
            database_url=self.database_url,
        )
        self.ticket_repository = self.repositories.tickets
        self.decision_repository = self.repositories.decisions
        self.answer_repository = self.repositories.answers
        self.retrieval_result_repository = (
            self.repositories.retrieval_results
        )

        self.classifier = RuleBasedTicketClassifier()
        self.pii_detector = RegexPiiDetector()
        self.risk_policy = RiskPolicy()

        self.llm_backend = os.getenv("LLM_BACKEND", "mock")
        self.llm_available = True
        self.llm_error: str | None = None
        self.generator_name = "celery-worker"
        self.generator_version = "delegated"

        self.generate_answer_use_case = None

        if self.queue_backend != "celery":
            retriever = TfidfKnowledgeBaseRetriever.from_json(
                default_knowledge_base_path()
            )

            try:
                generator = build_answer_generator()
            except LLMUnavailableError as exc:
                self.llm_available = False
                self.llm_error = str(exc)
                generator = UnavailableAnswerGenerator(
                    reason=str(exc),
                    requested_model=os.getenv("QWEN_MODEL_ID"),
                )

            self.generator_name = generator.name
            self.generator_version = generator.version

            self.generate_answer_use_case = GenerateAnswerUseCase(
                ticket_repository=self.ticket_repository,
                decision_repository=self.decision_repository,
                answer_repository=self.answer_repository,
                retrieval_result_repository=(
                    self.retrieval_result_repository
                ),
                retriever=retriever,
                generator=generator,
                safety_checker=DeterministicSafetyChecker(),
                retrieval_score_threshold=0.15,
                metrics=self.metrics,
            )

        self.generation_queue: GenerationQueue = self._build_queue()

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
            retrieval_result_repository=self.retrieval_result_repository,
        )

    @property
    def generation_status(self) -> str:
        if self.queue_backend == "celery":
            return "delegated"
        return "ready" if self.llm_available else "degraded"

    def close(self) -> None:
        close = getattr(self.generation_queue, "close", None)
        if callable(close):
            close()
        self.repositories.close()

    def _build_queue(self) -> GenerationQueue:
        if self.queue_backend == "celery":
            from support_ai.infrastructure.celery_app import celery_app

            return build_generation_queue(
                "celery",
                celery_client=celery_app,
                metrics=self.metrics,
            )

        if self.queue_backend == "memory":
            return build_generation_queue(
                "memory",
                metrics=self.metrics,
            )

        if self.queue_backend == "local":
            if self.generate_answer_use_case is None:
                raise RuntimeError(
                    "local queue requires generation use case"
                )
            return build_generation_queue(
                "local",
                handler=self.generate_answer_use_case.execute,
                metrics=self.metrics,
            )

        raise ValueError(
            f"Unsupported QUEUE_BACKEND: {self.queue_backend}"
        )


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
