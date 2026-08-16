from time import perf_counter
from uuid import UUID

from support_ai.application.observability import ensure_metrics
from support_ai.application.ports.contracts import (
    AnswerGenerator,
    AnswerRepository,
    DecisionRepository,
    Retriever,
    SafetyChecker,
    TicketRepository,
)
from support_ai.application.ports.observability import MetricsRecorder
from support_ai.domain.entities import Answer, Decision
from support_ai.domain.enums import (
    AnswerSource,
    AnswerStatus,
    DecisionReason,
    HandlingRoute,
)


class LLMUnavailableError(RuntimeError):
    pass


class GenerateAnswerUseCase:
    def __init__(
        self,
        *,
        ticket_repository: TicketRepository,
        decision_repository: DecisionRepository,
        answer_repository: AnswerRepository,
        retriever: Retriever,
        generator: AnswerGenerator,
        safety_checker: SafetyChecker,
        retrieval_score_threshold: float = 0.15,
        policy_version: str = "v1",
        metrics: MetricsRecorder | None = None,
    ) -> None:
        if not 0.0 <= retrieval_score_threshold <= 1.0:
            raise ValueError("retrieval_score_threshold must be in [0, 1]")

        self._ticket_repository = ticket_repository
        self._decision_repository = decision_repository
        self._answer_repository = answer_repository
        self._retriever = retriever
        self._generator = generator
        self._safety_checker = safety_checker
        self._retrieval_score_threshold = retrieval_score_threshold
        self._policy_version = policy_version
        self._metrics = ensure_metrics(metrics)

    def execute(self, ticket_id: UUID) -> Answer | None:
        total_started = perf_counter()

        ticket = self._ticket_repository.get(ticket_id)

        if ticket.route is not HandlingRoute.LLM:
            raise ValueError("ticket is not routed to LLM")

        ticket.mark_processing()
        self._ticket_repository.save(ticket)

        started = perf_counter()
        retrieved = self._retriever.retrieve(ticket.text, top_k=3)
        self._observe("generation.retrieval_ms", started)

        if (
            not retrieved
            or retrieved[0].score < self._retrieval_score_threshold
        ):
            self._metrics.increment(
                "generation.fallback.insufficient_retrieval_context"
            )
            self._fallback_to_human(
                ticket=ticket,
                reason=DecisionReason.INSUFFICIENT_RETRIEVAL_CONTEXT,
            )
            self._observe("generation.total_ms", total_started)
            return None

        context = [document.text for document in retrieved]

        try:
            started = perf_counter()
            generated_text = self._generator.generate(
                ticket_text=ticket.text,
                context=context,
            )
            self._observe("generation.llm_ms", started)
        except LLMUnavailableError:
            self._observe("generation.llm_ms", started)
            self._metrics.increment(
                "generation.fallback.llm_unavailable"
            )
            self._fallback_to_human(
                ticket=ticket,
                reason=DecisionReason.LLM_UNAVAILABLE,
            )
            self._observe("generation.total_ms", total_started)
            return None

        if generated_text.strip() == "NEED_HUMAN_REVIEW":
            self._metrics.increment(
                "generation.fallback.generator_abstained"
            )
            self._fallback_to_human(
                ticket=ticket,
                reason=DecisionReason.GENERATOR_ABSTAINED,
            )
            self._observe("generation.total_ms", total_started)
            return None

        answer = Answer(
            ticket_id=ticket.id,
            text=generated_text,
            source=AnswerSource.LLM,
            model_name=self._generator.name,
            model_version=self._generator.version,
        )

        started = perf_counter()
        is_safe = self._safety_checker.is_safe(generated_text)
        self._observe("generation.safety_ms", started)

        if not is_safe:
            started = perf_counter()
            answer.status = AnswerStatus.REJECTED
            self._answer_repository.add(answer)
            self._fallback_to_human(
                ticket=ticket,
                reason=DecisionReason.UNSAFE_GENERATED_RESPONSE,
            )
            self._observe("generation.persistence_ms", started)
            self._metrics.increment(
                "generation.fallback.unsafe_generated_response"
            )
            self._observe("generation.total_ms", total_started)
            return answer

        started = perf_counter()
        answer.status = AnswerStatus.SENT
        self._answer_repository.add(answer)
        ticket.mark_resolved()
        self._ticket_repository.save(ticket)
        self._observe("generation.persistence_ms", started)

        self._metrics.increment("generation.result.sent")
        self._observe("generation.total_ms", total_started)

        return answer

    def _fallback_to_human(
        self,
        *,
        ticket,
        reason: DecisionReason,
    ) -> None:
        ticket.escalate_to_human()
        self._ticket_repository.save(ticket)

        decision = Decision(
            ticket_id=ticket.id,
            category=ticket.category,
            confidence=ticket.category_confidence,
            risk_level=ticket.risk_level,
            route=HandlingRoute.HUMAN,
            reason=reason,
            classifier_name="n/a",
            classifier_version="n/a",
            policy_version=self._policy_version,
        )
        self._decision_repository.add(decision)

    def _observe(self, name: str, started: float) -> None:
        self._metrics.observe(
            name,
            (perf_counter() - started) * 1000,
        )
