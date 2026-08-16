from fastapi.testclient import TestClient

from support_ai.infrastructure.api.app import create_app
from support_ai.infrastructure.api.dependencies import reset_container


def make_client() -> TestClient:
    reset_container()
    return TestClient(create_app())


def test_runtime_safe_account_ticket_routes_to_llm():
    client = make_client()

    response = client.post(
        "/tickets",
        json={
            "external_id": "web-safe-1",
            "channel": "web",
            "text": "Как поменять пароль?",
            "user_id": "user-1",
            "metadata": {
                "language": "ru",
                "client": "web"
            }
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["category"] == "account"
    assert payload["confidence"] >= 0.80
    assert payload["risk_level"] == "low"
    assert payload["route"] == "llm"
    assert payload["reason"] == "safe_automation"


def test_runtime_payment_ticket_routes_to_human():
    client = make_client()

    response = client.post(
        "/tickets",
        json={
            "external_id": "chat-risk-1",
            "channel": "chat",
            "text": "С моей карты списали деньги без моего согласия",
            "user_id": "user-2",
            "metadata": {
                "language": "ru",
                "client": "web"
            }
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["category"] == "payment"
    assert payload["risk_level"] == "high"
    assert payload["route"] == "human"
    assert payload["reason"] == "high_risk_category"


def test_runtime_pii_forces_human_even_for_safe_category():
    client = make_client()

    response = client.post(
        "/tickets",
        json={
            "external_id": "email-pii-1",
            "channel": "email",
            "text": "Как поменять пароль? Ответьте на user@example.com",
            "user_id": "user-3",
            "metadata": {
                "language": "ru",
                "client": "web"
            }
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["category"] == "account"
    assert payload["risk_level"] == "high"
    assert payload["route"] == "human"
    assert payload["reason"] == "pii_detected"


def test_runtime_unknown_ticket_abstains_to_human():
    client = make_client()

    response = client.post(
        "/tickets",
        json={
            "external_id": "mobile-unknown-1",
            "channel": "mobile",
            "text": "Вчера опять было как тогда",
            "user_id": "user-4",
            "metadata": {
                "language": "ru",
                "client": "android"
            }
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["category"] == "other"
    assert payload["confidence"] < 0.80
    assert payload["route"] == "human"
    assert payload["reason"] == "low_confidence"
