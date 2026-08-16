from typing import Protocol
from uuid import UUID


class CeleryClient(Protocol):
    def send_task(
        self,
        name: str,
        args: list[str] | None = None,
        kwargs: dict | None = None,
        *,
        queue: str | None = None,
    ):
        ...


class CeleryGenerationQueue:
    """Celery adapter for the application GenerationQueue port.

    The adapter intentionally depends only on the tiny `send_task` surface,
    which keeps it easy to test without a running broker.
    """

    TASK_NAME = "support_ai.generate_answer"
    DEFAULT_QUEUE = "response_generation"

    def __init__(
        self,
        celery_client: CeleryClient,
        *,
        queue_name: str = DEFAULT_QUEUE,
    ) -> None:
        self._celery_client = celery_client
        self._queue_name = queue_name

    def enqueue(self, ticket_id: UUID) -> None:
        self._celery_client.send_task(
            self.TASK_NAME,
            args=[str(ticket_id)],
            queue=self._queue_name,
        )
