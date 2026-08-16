import pytest

from support_ai.adapters.in_memory import FakeGenerationQueue
from support_ai.adapters.queue import CeleryGenerationQueue, LocalGenerationQueue
from support_ai.infrastructure.queue_factory import build_generation_queue


class FakeCeleryClient:
    def send_task(self, name, args=None, kwargs=None, *, queue=None):
        return object()


def test_memory_queue_backend_builds_fake_queue():
    queue = build_generation_queue("memory")

    assert isinstance(queue, FakeGenerationQueue)


def test_celery_queue_backend_builds_celery_adapter():
    queue = build_generation_queue(
        "celery",
        celery_client=FakeCeleryClient(),
    )

    assert isinstance(queue, CeleryGenerationQueue)


def test_celery_backend_requires_client():
    with pytest.raises(ValueError, match="celery_client is required"):
        build_generation_queue("celery")


def test_local_queue_backend_builds_local_adapter():
    queue = build_generation_queue(
        "local",
        handler=lambda ticket_id: None,
    )

    try:
        assert isinstance(queue, LocalGenerationQueue)
    finally:
        queue.close()


def test_local_backend_requires_handler():
    with pytest.raises(ValueError, match="handler is required"):
        build_generation_queue("local")
