from support_ai.adapters.in_memory import (
    FakeClassifier,
    FakeGenerationQueue,
    FakePiiDetector,
    InMemoryDecisionRepository,
    InMemoryTicketRepository,
)
from support_ai.application.use_cases.process_ticket import ProcessTicketUseCase
from support_ai.domain.enums import Channel, DecisionReason, HandlingRoute, TicketCategory
from support_ai.domain.policies import RiskPolicy


def build_use_case(*, classifier, pii_detector=None):
    ticket_repo = InMemoryTicketRepository()
    decision_repo = InMemoryDecisionRepository()
    queue = FakeGenerationQueue()

    use_case = ProcessTicketUseCase(
        classifier=classifier,
        pii_detector=pii_detector or FakePiiDetector(False),
        risk_policy=RiskPolicy(),
        ticket_repository=ticket_repo,
        decision_repository=decision_repo,
        generation_queue=queue,
    )
    return use_case, ticket_repo, decision_repo, queue


def test_safe_ticket_is_persisted_audited_and_enqueued():
    use_case, ticket_repo, decision_repo, queue = build_use_case(
        classifier=FakeClassifier(TicketCategory.FAQ, 0.95)
    )

    result = use_case.execute(
        external_id="web-42",
        text="Как поменять пароль?",
        channel=Channel.WEB,
        user_id="user-1",
        metadata={
            "app_version": "1.2.3",
            "language": "ru",
        },
    )

    assert result.ticket.external_id == "web-42"
    assert result.ticket.user_id == "user-1"
    assert result.ticket.metadata == {
        "app_version": "1.2.3",
        "language": "ru",
    }
    assert result.ticket.route is HandlingRoute.LLM
    assert result.ticket.id in ticket_repo.items
    assert queue.items == [result.ticket.id]
    assert len(decision_repo.items) == 1
    assert decision_repo.items[0].reason is DecisionReason.SAFE_AUTOMATION


def test_risky_ticket_is_never_enqueued_for_llm():
    use_case, _, decision_repo, queue = build_use_case(
        classifier=FakeClassifier(TicketCategory.PAYMENT, 0.99)
    )

    result = use_case.execute(
        external_id="chat-99",
        text="С моей карты списали 30000 рублей",
        channel=Channel.CHAT,
    )

    assert result.ticket.route is HandlingRoute.HUMAN
    assert queue.items == []
    assert decision_repo.items[0].reason is DecisionReason.HIGH_RISK_CATEGORY
