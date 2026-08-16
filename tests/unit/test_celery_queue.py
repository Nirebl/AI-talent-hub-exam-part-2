from uuid import uuid4

from support_ai.adapters.queue.celery_queue import CeleryGenerationQueue


class FakeCeleryClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send_task(
        self,
        name: str,
        args=None,
        kwargs=None,
        *,
        queue=None,
    ):
        self.calls.append(
            {
                "name": name,
                "args": args,
                "kwargs": kwargs,
                "queue": queue,
            }
        )
        return object()


def test_celery_generation_queue_sends_expected_task():
    client = FakeCeleryClient()
    queue = CeleryGenerationQueue(client)
    ticket_id = uuid4()

    queue.enqueue(ticket_id)

    assert client.calls == [
        {
            "name": "support_ai.generate_answer",
            "args": [str(ticket_id)],
            "kwargs": None,
            "queue": "response_generation",
        }
    ]


def test_celery_generation_queue_supports_custom_queue_name():
    client = FakeCeleryClient()
    queue = CeleryGenerationQueue(client, queue_name="high_priority")
    ticket_id = uuid4()

    queue.enqueue(ticket_id)

    assert client.calls[0]["queue"] == "high_priority"
