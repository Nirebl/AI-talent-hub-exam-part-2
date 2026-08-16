from typing import Protocol, Sequence
from uuid import UUID

from support_ai.application.models import RetrievedDocument
from support_ai.domain.entities import Prediction


class TicketClassifier(Protocol):
    name: str
    version: str

    def predict(self, text: str) -> Prediction:
        ...


class PiiDetector(Protocol):
    def contains_pii(self, text: str) -> bool:
        ...


class GenerationQueue(Protocol):
    def enqueue(self, ticket_id: UUID) -> None:
        ...


class Retriever(Protocol):
    name: str
    version: str

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 3,
    ) -> Sequence[RetrievedDocument]:
        ...


class AnswerGenerator(Protocol):
    name: str
    version: str

    def generate(
        self,
        *,
        ticket_text: str,
        context: Sequence[str],
    ) -> str:
        ...


class SafetyChecker(Protocol):
    def is_safe(self, text: str) -> bool:
        ...
