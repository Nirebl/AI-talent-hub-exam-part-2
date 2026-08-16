import os

from celery import Celery


def create_celery_app() -> Celery:
    broker_url = os.getenv(
        "CELERY_BROKER_URL",
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )

    app = Celery(
        "support_ai",
        broker=broker_url,
        include=["support_ai.infrastructure.workers.tasks"],
    )

    app.conf.update(
        task_default_queue="response_generation",
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        broker_connection_retry_on_startup=True,
        worker_prefetch_multiplier=1,
        task_routes={
            "support_ai.generate_answer": {
                "queue": "response_generation",
            }
        },
    )
    return app


celery_app = create_celery_app()
