import pytest

from support_ai.adapters.in_memory import FakeGenerationQueue
from support_ai.adapters.queue.celery_queue import CeleryGenerationQueue
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
