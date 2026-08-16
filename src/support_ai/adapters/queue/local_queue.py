from __future__ import annotations

from collections.abc import Callable
from queue import Queue
from threading import Lock, Thread
from time import perf_counter
from uuid import UUID

from support_ai.application.observability import ensure_metrics
from support_ai.application.ports.observability import MetricsRecorder


class LocalGenerationQueue:
    def __init__(
        self,
        handler: Callable[[UUID], object],
        *,
        metrics: MetricsRecorder | None = None,
    ) -> None:
        self._handler = handler
        self._metrics = ensure_metrics(metrics)
        self._queue: Queue[tuple[UUID, float] | None] = Queue()
        self._errors: list[tuple[UUID, Exception]] = []
        self._errors_lock = Lock()
        self._closed = False
        self._thread = Thread(
            target=self._run,
            name="local-generation-worker",
            daemon=True,
        )
        self._thread.start()

    @property
    def errors(self) -> tuple[tuple[UUID, Exception], ...]:
        with self._errors_lock:
            return tuple(self._errors)

    def enqueue(self, ticket_id: UUID) -> None:
        if self._closed:
            raise RuntimeError("local generation queue is closed")
        self._queue.put((ticket_id, perf_counter()))

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._queue.put(None)
        self._thread.join(timeout=5)

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is None:
                    return

                ticket_id, enqueued_at = item
                self._metrics.observe(
                    "generation.queue_wait_ms",
                    (perf_counter() - enqueued_at) * 1000,
                )
                self._handler(ticket_id)
            except Exception as exc:
                if item is not None:
                    ticket_id, _ = item
                    with self._errors_lock:
                        self._errors.append((ticket_id, exc))
                    self._metrics.increment(
                        "generation.worker.unhandled_error"
                    )
            finally:
                self._queue.task_done()
