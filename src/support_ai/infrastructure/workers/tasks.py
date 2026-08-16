from support_ai.infrastructure.celery_app import celery_app
from support_ai.infrastructure.workers.dependencies import (
    get_generate_answer_use_case,
)
from support_ai.infrastructure.workers.runner import run_generate_answer


@celery_app.task(
    name="support_ai.generate_answer",
    bind=True,
    autoretry_for=(RuntimeError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def generate_answer(self, ticket_id: str) -> None:
    """Celery entry point for asynchronous answer generation."""

    use_case = get_generate_answer_use_case()
    run_generate_answer(
        ticket_id=ticket_id,
        use_case=use_case,
    )
