from __future__ import annotations

from collections.abc import Callable
from typing import Literal
from uuid import UUID

from support_ai.adapters.in_memory import FakeGenerationQueue
from support_ai.adapters.queue import (
    CeleryGenerationQueue,
    LocalGenerationQueue,
)
from support_ai.application.ports.observability import MetricsRecorder
from support_ai.application.ports.services import GenerationQueue

QueueBackend = Literal["memory", "local", "celery"]


def build_generation_queue(
    backend: QueueBackend = "memory",
    *,
    handler: Callable[[UUID], object] | None = None,
    celery_client=None,
    metrics: MetricsRecorder | None = None,
) -> GenerationQueue:
    if backend == "memory":
        return FakeGenerationQueue()

    if backend == "local":
        if handler is None:
            raise ValueError("handler is required for local backend")
        return LocalGenerationQueue(
            handler,
            metrics=metrics,
        )

    if backend == "celery":
        if celery_client is None:
            raise ValueError("celery_client is required for celery backend")
        return CeleryGenerationQueue(celery_client)

    raise ValueError(f"Unsupported queue backend: {backend}")
