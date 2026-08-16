import os


def warm_generation_worker() -> None:
    if os.getenv("LLM_BACKEND", "mock") != "qwen":
        return

    from support_ai.infrastructure.workers.dependencies import (
        get_worker_container,
    )

    get_worker_container()
