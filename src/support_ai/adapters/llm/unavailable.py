from typing import Sequence

from support_ai.application.use_cases.generate_answer import LLMUnavailableError


class UnavailableAnswerGenerator:
    name = "unavailable-generator"

    def __init__(
        self,
        *,
        reason: str,
        requested_model: str | None = None,
    ) -> None:
        self.reason = reason
        self.version = requested_model or "unavailable"

    def generate(
        self,
        *,
        ticket_text: str,
        context: Sequence[str],
    ) -> str:
        raise LLMUnavailableError(self.reason)
