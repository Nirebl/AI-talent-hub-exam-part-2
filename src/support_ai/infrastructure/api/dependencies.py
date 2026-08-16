from functools import lru_cache

from support_ai.adapters.in_memory import (
    FakeGenerationQueue,
    InMemoryDecisionRepository,
    InMemoryTicketRepository,
)
from support_ai.adapters.ml import (
    RegexPiiDetector,
    RuleBasedTicketClassifier,
)
from support_ai.application.ports.repositories import (
    DecisionRepository,
    TicketRepository,
)
from support_ai.application.ports.services import (
    GenerationQueue,
    PiiDetector,
    TicketClassifier,
)
from support_ai.application.use_cases.process_ticket import ProcessTicketUseCase
from support_ai.domain.policies import RiskPolicy


class AppContainer:
    """Composition root for the current local PoC."""

    def __init__(self) -> None:
        self.ticket_repository: TicketRepository = InMemoryTicketRepository()
        self.decision_repository: DecisionRepository = InMemoryDecisionRepository()
        self.generation_queue: GenerationQueue = FakeGenerationQueue()

        self.classifier: TicketClassifier = RuleBasedTicketClassifier()
        self.pii_detector: PiiDetector = RegexPiiDetector()
        self.risk_policy = RiskPolicy()

        self.process_ticket_use_case = ProcessTicketUseCase(
            classifier=self.classifier,
            pii_detector=self.pii_detector,
            risk_policy=self.risk_policy,
            ticket_repository=self.ticket_repository,
            decision_repository=self.decision_repository,
            generation_queue=self.generation_queue,
        )


@lru_cache
def get_container() -> AppContainer:
    return AppContainer()


def get_process_ticket_use_case() -> ProcessTicketUseCase:
    return get_container().process_ticket_use_case
