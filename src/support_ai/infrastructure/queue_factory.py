from __future__ import annotations

from typing import Literal

from support_ai.adapters.in_memory import FakeGenerationQueue
from support_ai.adapters.queue.celery_queue import CeleryGenerationQueue
from support_ai.application.ports.services import GenerationQueue

QueueBackend = Literal["memory", "celery"]


def build_generation_queue(
    backend: QueueBackend = "memory",
    *,
    celery_client=None,
) -> GenerationQueue:
    if backend == "memory":
        return FakeGenerationQueue()

    if backend == "celery":
        if celery_client is None:
            raise ValueError("celery_client is required for celery backend")
        return CeleryGenerationQueue(celery_client)

    raise ValueError(f"Unsupported queue backend: {backend}")
