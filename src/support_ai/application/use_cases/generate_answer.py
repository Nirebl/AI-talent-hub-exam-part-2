from uuid import UUID

from support_ai.application.ports.contracts import (
    AnswerGenerator,
    AnswerRepository,
    DecisionRepository,
    Retriever,
    SafetyChecker,
    TicketRepository,
)
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

    def execute(self, ticket_id: UUID) -> Answer | None:
        ticket = self._ticket_repository.get(ticket_id)

        if ticket.route is not HandlingRoute.LLM:
            raise ValueError("ticket is not routed to LLM")

        ticket.mark_processing()
        self._ticket_repository.save(ticket)

        retrieved = self._retriever.retrieve(ticket.text, top_k=3)

        if (
            not retrieved
            or retrieved[0].score < self._retrieval_score_threshold
        ):
            self._fallback_to_human(
                ticket=ticket,
                reason=DecisionReason.INSUFFICIENT_RETRIEVAL_CONTEXT,
            )
            return None

        context = [document.text for document in retrieved]

        try:
            generated_text = self._generator.generate(
                ticket_text=ticket.text,
                context=context,
            )
        except LLMUnavailableError:
            self._fallback_to_human(
                ticket=ticket,
                reason=DecisionReason.LLM_UNAVAILABLE,
            )
            return None

        if generated_text.strip() == "NEED_HUMAN_REVIEW":
            self._fallback_to_human(
                ticket=ticket,
                reason=DecisionReason.GENERATOR_ABSTAINED,
            )
            return None

        answer = Answer(
            ticket_id=ticket.id,
            text=generated_text,
            source=AnswerSource.LLM,
            model_name=self._generator.name,
            model_version=self._generator.version,
        )

        if not self._safety_checker.is_safe(generated_text):
            answer.status = AnswerStatus.REJECTED
            self._answer_repository.add(answer)
            self._fallback_to_human(
                ticket=ticket,
                reason=DecisionReason.UNSAFE_GENERATED_RESPONSE,
            )
            return answer

        answer.status = AnswerStatus.SENT
        self._answer_repository.add(answer)
        ticket.mark_resolved()
        self._ticket_repository.save(ticket)
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
