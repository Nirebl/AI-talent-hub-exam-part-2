from support_ai.adapters.in_memory import (
    InMemoryAnswerRepository,
    InMemoryDecisionRepository,
    InMemoryTicketRepository,
)
from support_ai.infrastructure.persistence_factory import build_repositories


def test_memory_backend_builds_in_memory_repositories():
    bundle = build_repositories("memory")

    assert isinstance(bundle.tickets, InMemoryTicketRepository)
    assert isinstance(bundle.decisions, InMemoryDecisionRepository)
    assert isinstance(bundle.answers, InMemoryAnswerRepository)
