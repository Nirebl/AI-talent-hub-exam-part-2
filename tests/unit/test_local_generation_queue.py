from threading import Event
from uuid import uuid4

from support_ai.adapters.queue import LocalGenerationQueue


def test_local_generation_queue_invokes_handler():
    completed = Event()
    received = []

    def handler(ticket_id):
        received.append(ticket_id)
        completed.set()

    queue = LocalGenerationQueue(handler)
    ticket_id = uuid4()

    try:
        queue.enqueue(ticket_id)

        assert completed.wait(timeout=1)
        assert received == [ticket_id]
        assert queue.errors == ()
    finally:
        queue.close()


def test_local_generation_queue_keeps_running_after_handler_error():
    completed = Event()
    calls = []

    def handler(ticket_id):
        calls.append(ticket_id)
        if len(calls) == 1:
            raise RuntimeError("boom")
        completed.set()

    queue = LocalGenerationQueue(handler)
    first = uuid4()
    second = uuid4()

    try:
        queue.enqueue(first)
        queue.enqueue(second)

        assert completed.wait(timeout=1)
        assert calls == [first, second]
        assert len(queue.errors) == 1
        assert queue.errors[0][0] == first
    finally:
        queue.close()
