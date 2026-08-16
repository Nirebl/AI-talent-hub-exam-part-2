from __future__ import annotations

import os
from typing import Literal

from support_ai.application.ports.services import AnswerGenerator

from .mock import MockAnswerGenerator
from .qwen import QwenAnswerGenerator, QwenGenerationConfig

LLMBackend = Literal["mock", "qwen"]


def build_answer_generator(
    backend: LLMBackend | None = None,
) -> AnswerGenerator:
    selected_backend = backend or os.getenv("LLM_BACKEND", "mock")

    if selected_backend == "mock":
        return MockAnswerGenerator()

    if selected_backend == "qwen":
        config = QwenGenerationConfig(
            model_id=os.getenv(
                "QWEN_MODEL_ID",
                "Qwen/Qwen3-4B-Instruct-2507",
            ),
            max_new_tokens=int(
                os.getenv("QWEN_MAX_NEW_TOKENS", "256")
            ),
            max_input_tokens=int(
                os.getenv("QWEN_MAX_INPUT_TOKENS", "4096")
            ),
            load_in_4bit=os.getenv(
                "QWEN_LOAD_IN_4BIT",
                "true",
            ).lower() in {"1", "true", "yes"},
        )
        return QwenAnswerGenerator.from_pretrained(config)

    raise ValueError(
        f"Unsupported LLM backend: {selected_backend}"
    )
