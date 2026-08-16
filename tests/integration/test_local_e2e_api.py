import time

from fastapi.testclient import TestClient

from support_ai.infrastructure.api.app import create_app
from support_ai.infrastructure.api.dependencies import reset_container


def wait_for_terminal_state(
    client: TestClient,
    ticket_id: str,
    *,
    timeout: float = 2.0,
):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/tickets/{ticket_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] == "resolved":
            return payload
        if payload["route"] == "human":
            return payload
        time.sleep(0.01)
    raise AssertionError("ticket did not reach a terminal PoC state")


def test_local_runtime_processes_safe_ticket_end_to_end(monkeypatch):
    monkeypatch.setenv("QUEUE_BACKEND", "local")
    monkeypatch.setenv("LLM_BACKEND", "mock")
    reset_container()

    try:
        client = TestClient(create_app())

        created = client.post(
            "/tickets",
            json={
                "external_id": "e2e-safe-1",
                "channel": "web",
                "text": "Как поменять пароль?",
                "user_id": "user-1",
                "metadata": {
                    "language": "ru",
                    "client": "web"
                }
            },
        )

        assert created.status_code == 201
        assert created.json()["route"] == "llm"

        result = wait_for_terminal_state(
            client,
            created.json()["ticket_id"],
        )

        assert result["status"] == "resolved"
        assert result["route"] == "llm"
        assert result["answer"] is not None
        assert result["answer"]["source"] == "llm"
        assert result["answer"]["status"] == "sent"
        assert "Password reset" in result["answer"]["text"]
    finally:
        reset_container()


def test_local_runtime_keeps_high_risk_ticket_on_human(monkeypatch):
    monkeypatch.setenv("QUEUE_BACKEND", "local")
    monkeypatch.setenv("LLM_BACKEND", "mock")
    reset_container()

    try:
        client = TestClient(create_app())

        created = client.post(
            "/tickets",
            json={
                "external_id": "e2e-risk-1",
                "channel": "chat",
                "text": "С моей карты списали деньги без моего согласия",
                "user_id": "user-2",
                "metadata": {
                    "language": "ru",
                    "client": "web"
                }
            },
        )

        ticket_id = created.json()["ticket_id"]
        result = client.get(f"/tickets/{ticket_id}")

        assert result.status_code == 200
        payload = result.json()
        assert payload["status"] == "pending"
        assert payload["route"] == "human"
        assert payload["reason"] == "high_risk_category"
        assert payload["answer"] is None
    finally:
        reset_container()
