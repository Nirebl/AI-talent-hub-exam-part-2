from dataclasses import dataclass
from time import perf_counter
from typing import Any

from support_ai.application.observability import ensure_metrics
from support_ai.application.ports.contracts import (
    DecisionRepository,
    GenerationQueue,
    PiiDetector,
    TicketClassifier,
    TicketRepository,
)
from support_ai.application.ports.observability import MetricsRecorder
from support_ai.domain.entities import Decision, Ticket
from support_ai.domain.enums import Channel, HandlingRoute
from support_ai.domain.policies import RiskPolicy


@dataclass(frozen=True, slots=True)
class ProcessTicketResult:
    ticket: Ticket
    decision: Decision


class ProcessTicketUseCase:
    def __init__(
        self,
        *,
        classifier: TicketClassifier,
        pii_detector: PiiDetector,
        risk_policy: RiskPolicy,
        ticket_repository: TicketRepository,
        decision_repository: DecisionRepository,
        generation_queue: GenerationQueue,
        metrics: MetricsRecorder | None = None,
    ) -> None:
        self._classifier = classifier
        self._pii_detector = pii_detector
        self._risk_policy = risk_policy
        self._ticket_repository = ticket_repository
        self._decision_repository = decision_repository
        self._generation_queue = generation_queue
        self._metrics = ensure_metrics(metrics)

    def execute(
        self,
        *,
        text: str,
        channel: Channel,
        external_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProcessTicketResult:
        total_started = perf_counter()

        ticket = Ticket(
            text=text,
            channel=channel,
            external_id=external_id,
            user_id=user_id,
            metadata=metadata or {},
        )

        started = perf_counter()
        prediction = self._classifier.predict(ticket.classifier_text)
        self._observe("routing.classification_ms", started)

        started = perf_counter()
        contains_pii = self._pii_detector.contains_pii(ticket.classifier_text)
        self._observe("routing.pii_detection_ms", started)

        started = perf_counter()
        outcome = self._risk_policy.decide(
            prediction=prediction,
            contains_pii=contains_pii,
        )
        self._observe("routing.policy_ms", started)

        ticket.apply_routing(
            prediction=prediction,
            route=outcome.route,
            risk_level=outcome.risk_level,
            contains_pii=contains_pii,
        )

        decision = Decision(
            ticket_id=ticket.id,
            category=prediction.category,
            confidence=prediction.confidence,
            risk_level=outcome.risk_level,
            route=outcome.route,
            reason=outcome.reason,
            classifier_name=self._classifier.name,
            classifier_version=self._classifier.version,
            policy_version=self._risk_policy.policy_version,
        )

        started = perf_counter()
        self._ticket_repository.add(ticket)
        self._decision_repository.add(decision)
        self._observe("routing.persistence_ms", started)

        self._metrics.increment(f"routing.route.{outcome.route.value}")
        self._metrics.increment(f"routing.reason.{outcome.reason.value}")

        if outcome.route is HandlingRoute.LLM:
            started = perf_counter()
            self._generation_queue.enqueue(ticket.id)
            self._observe("routing.enqueue_ms", started)

        self._observe("routing.total_ms", total_started)

        return ProcessTicketResult(
            ticket=ticket,
            decision=decision,
        )

    def _observe(self, name: str, started: float) -> None:
        self._metrics.observe(
            name,
            (perf_counter() - started) * 1000,
        )
