from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from support_ai.infrastructure.api.app import create_app
from support_ai.infrastructure.api.dependencies import get_container


CASES = [
    {
        "name": "happy_path",
        "payload": {
            "external_id": "web-1",
            "channel": "web",
            "text": "Как поменять пароль?",
            "user_id": "user-1",
            "metadata": {
                "language": "ru",
                "client": "web"
            }
        },
    },
    {
        "name": "risky_path",
        "payload": {
            "external_id": "chat-1",
            "channel": "chat",
            "text": "С моей карты списали деньги без моего согласия",
            "user_id": "user-2",
            "metadata": {
                "language": "ru",
                "client": "web"
            }
        },
    },
    {
        "name": "pii_fallback",
        "payload": {
            "external_id": "email-1",
            "channel": "email",
            "text": "Как поменять пароль? Ответьте на user@example.com",
            "user_id": "user-3",
            "metadata": {
                "language": "ru",
                "client": "web"
            }
        },
    },
]


def main() -> None:
    get_container.cache_clear()
    client = TestClient(create_app())

    for case in CASES:
        response = client.post("/tickets", json=case["payload"])
        print(case["name"])
        print(response.json())
        print()


if __name__ == "__main__":
    main()
