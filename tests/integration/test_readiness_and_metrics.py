import time

from fastapi.testclient import TestClient

from support_ai.application.use_cases.generate_answer import LLMUnavailableError
from support_ai.infrastructure.api import dependencies
from support_ai.infrastructure.api.app import create_app


def test_ready_reports_healthy_generation(monkeypatch):
    monkeypatch.setenv("QUEUE_BACKEND", "local")
    monkeypatch.setenv("LLM_BACKEND", "mock")
    dependencies.reset_container()

    try:
        with TestClient(create_app()) as client:
            response = client.get("/ready")

            assert response.status_code == 200
            payload = response.json()
            assert payload["status"] == "ready"
            assert payload["generation_status"] == "ready"
            assert payload["llm_available"] is True
            assert payload["llm_backend"] == "mock"
    finally:
        dependencies.reset_container()


def test_llm_startup_failure_degrades_to_human(monkeypatch):
    monkeypatch.setenv("QUEUE_BACKEND", "local")
    monkeypatch.setenv("LLM_BACKEND", "qwen")

    def fail_generator():
        raise LLMUnavailableError("model failed to load")

    monkeypatch.setattr(
        dependencies,
        "build_answer_generator",
        fail_generator,
    )
    dependencies.reset_container()

    try:
        with TestClient(create_app()) as client:
            ready = client.get("/ready")
            assert ready.status_code == 200
            ready_payload = ready.json()
            assert ready_payload["status"] == "ready"
            assert ready_payload["generation_status"] == "degraded"
            assert ready_payload["llm_available"] is False
            assert ready_payload["llm_error"] == "model failed to load"

            created = client.post(
                "/tickets",
                json={
                    "external_id": "degraded-1",
                    "channel": "web",
                    "text": "Как поменять пароль?",
                    "metadata": {
                        "language": "ru",
                        "client": "web"
                    }
                },
            )
            assert created.status_code == 201
            ticket_id = created.json()["ticket_id"]

            deadline = time.monotonic() + 2.0
            result = None
            while time.monotonic() < deadline:
                current = client.get(f"/tickets/{ticket_id}")
                result = current.json()
                if result["route"] == "human":
                    break
                time.sleep(0.01)

            assert result is not None
            assert result["route"] == "human"
            assert result["status"] == "pending"
            assert result["reason"] == "llm_unavailable"
            assert result["answer"] is None
    finally:
        dependencies.reset_container()


def test_metrics_endpoint_exposes_stage_latency(monkeypatch):
    monkeypatch.setenv("QUEUE_BACKEND", "local")
    monkeypatch.setenv("LLM_BACKEND", "mock")
    dependencies.reset_container()

    try:
        with TestClient(create_app()) as client:
            created = client.post(
                "/tickets",
                json={
                    "external_id": "metrics-1",
                    "channel": "web",
                    "text": "Как поменять пароль?",
                    "metadata": {
                        "language": "ru",
                        "client": "web"
                    }
                },
            )
            assert created.status_code == 201
            ticket_id = created.json()["ticket_id"]

            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                current = client.get(f"/tickets/{ticket_id}").json()
                if current["status"] == "resolved":
                    break
                time.sleep(0.01)

            response = client.get("/metrics")
            assert response.status_code == 200
            payload = response.json()

            timing_names = payload["timings"].keys()
            assert "routing.classification_ms" in timing_names
            assert "routing.pii_detection_ms" in timing_names
            assert "routing.policy_ms" in timing_names
            assert "routing.total_ms" in timing_names
            assert "generation.queue_wait_ms" in timing_names
            assert "generation.retrieval_ms" in timing_names
            assert "generation.llm_ms" in timing_names
            assert "generation.safety_ms" in timing_names
            assert "generation.total_ms" in timing_names
            assert "http.request_ms" in timing_names
            assert payload["counters"]["routing.route.llm"] >= 1
            assert payload["counters"]["generation.result.sent"] >= 1
    finally:
        dependencies.reset_container()
