from fastapi.testclient import TestClient

from support_ai.adapters.in_memory import (
    FakeClassifier,
    FakeGenerationQueue,
    FakePiiDetector,
    InMemoryDecisionRepository,
    InMemoryTicketRepository,
)
from support_ai.application.use_cases.process_ticket import ProcessTicketUseCase
from support_ai.domain.enums import TicketCategory
from support_ai.domain.policies import RiskPolicy
from support_ai.infrastructure.api.app import create_app
from support_ai.infrastructure.api.dependencies import get_process_ticket_use_case


def build_use_case(*, category: TicketCategory, confidence: float, contains_pii: bool = False):
    ticket_repository = InMemoryTicketRepository()
    decision_repository = InMemoryDecisionRepository()
    queue = FakeGenerationQueue()

    use_case = ProcessTicketUseCase(
        classifier=FakeClassifier(category, confidence),
        pii_detector=FakePiiDetector(contains_pii),
        risk_policy=RiskPolicy(),
        ticket_repository=ticket_repository,
        decision_repository=decision_repository,
        generation_queue=queue,
    )
    return use_case, ticket_repository, decision_repository, queue


def test_health_endpoint():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_safe_ticket_endpoint_accepts_canonical_ticket_fields():
    use_case, ticket_repo, _, queue = build_use_case(
        category=TicketCategory.FAQ,
        confidence=0.95,
    )
    app = create_app()
    app.dependency_overrides[get_process_ticket_use_case] = lambda: use_case
    client = TestClient(app)

    response = client.post(
        "/tickets",
        json={
            "external_id": "email-23891",
            "channel": "email",
            "text": "Как поменять пароль?",
            "user_id": "user-731",
            "metadata": {
                "thread_id": "thread-918",
                "language": "ru",
                "client": "web"
            },
        },
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["external_id"] == "email-23891"
    assert payload["route"] == "llm"
    assert payload["category"] == "faq"
    assert payload["risk_level"] == "low"
    assert payload["reason"] == "safe_automation"
    assert len(queue.items) == 1

    persisted = next(iter(ticket_repo.items.values()))
    assert persisted.user_id == "user-731"
    assert persisted.metadata["thread_id"] == "thread-918"


def test_risky_ticket_endpoint_never_enqueues_for_llm():
    use_case, _, _, queue = build_use_case(
        category=TicketCategory.PAYMENT,
        confidence=0.99,
    )
    app = create_app()
    app.dependency_overrides[get_process_ticket_use_case] = lambda: use_case
    client = TestClient(app)

    response = client.post(
        "/tickets",
        json={
            "external_id": "chat-77",
            "text": "С моей карты списали 30000 рублей",
            "channel": "chat",
            "user_id": "user-2",
            "metadata": {
                "language": "ru"
            },
        },
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["route"] == "human"
    assert payload["category"] == "payment"
    assert payload["risk_level"] == "high"
    assert payload["reason"] == "high_risk_category"
    assert queue.items == []


def test_invalid_empty_ticket_is_rejected_by_api_schema():
    client = TestClient(create_app())

    response = client.post(
        "/tickets",
        json={
            "text": "",
            "channel": "web",
        },
    )

    assert response.status_code == 422


def test_invalid_channel_enum_is_rejected():
    client = TestClient(create_app())

    response = client.post(
        "/tickets",
        json={
            "channel": "telegram",
            "text": "Как поменять пароль?"
        },
    )

    assert response.status_code == 422


def test_invalid_metadata_enum_is_rejected():
    client = TestClient(create_app())

    response = client.post(
        "/tickets",
        json={
            "channel": "web",
            "text": "Как поменять пароль?",
            "metadata": {
                "language": "de",
                "client": "smart_tv"
            }
        },
    )

    assert response.status_code == 422


def test_unknown_request_fields_are_rejected():
    client = TestClient(create_app())

    response = client.post(
        "/tickets",
        json={
            "channel": "web",
            "text": "Как поменять пароль?",
            "route": "human"
        },
    )

    assert response.status_code == 422
