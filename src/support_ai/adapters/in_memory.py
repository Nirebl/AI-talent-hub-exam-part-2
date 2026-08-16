from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from support_ai.application.models import RetrievedDocument
from support_ai.application.use_cases.generate_answer import LLMUnavailableError
from support_ai.domain.entities import Answer, Decision, Prediction, Ticket
from support_ai.domain.enums import TicketCategory


class InMemoryTicketRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Ticket] = {}

    def add(self, ticket: Ticket) -> None:
        self.items[ticket.id] = ticket

    def get(self, ticket_id: UUID) -> Ticket:
        return self.items[ticket_id]

    def save(self, ticket: Ticket) -> None:
        self.items[ticket.id] = ticket


class InMemoryDecisionRepository:
    def __init__(self) -> None:
        self.items: list[Decision] = []

    def add(self, decision: Decision) -> None:
        self.items.append(decision)


class InMemoryAnswerRepository:
    def __init__(self) -> None:
        self.items: list[Answer] = []

    def add(self, answer: Answer) -> None:
        self.items.append(answer)


class FakeGenerationQueue:
    def __init__(self) -> None:
        self.items: list[UUID] = []

    def enqueue(self, ticket_id: UUID) -> None:
        self.items.append(ticket_id)


@dataclass(slots=True)
class FakeClassifier:
    category: TicketCategory
    confidence: float
    name: str = "fake-classifier"
    version: str = "test"

    def predict(self, text: str) -> Prediction:
        return Prediction(category=self.category, confidence=self.confidence)


@dataclass(slots=True)
class FakePiiDetector:
    result: bool = False

    def contains_pii(self, text: str) -> bool:
        return self.result


@dataclass(slots=True)
class FakeRetriever:
    documents: Sequence[str]
    score: float = 1.0

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 3,
    ) -> Sequence[RetrievedDocument]:
        return [
            RetrievedDocument(
                document_id=f"fake-{index}",
                text=text,
                score=self.score,
            )
            for index, text in enumerate(self.documents[:top_k])
        ]


@dataclass(slots=True)
class MockAnswerGenerator:
    answer: str
    name: str = "mock-generator"
    version: str = "test"

    def generate(self, *, ticket_text: str, context: Sequence[str]) -> str:
        return self.answer


@dataclass(slots=True)
class FailingAnswerGenerator:
    name: str = "failing-generator"
    version: str = "test"

    def generate(self, *, ticket_text: str, context: Sequence[str]) -> str:
        raise LLMUnavailableError("LLM backend unavailable")


@dataclass(slots=True)
class FakeSafetyChecker:
    safe: bool = True

    def is_safe(self, text: str) -> bool:
        return self.safe
