from dataclasses import dataclass
from typing import Sequence


@dataclass(slots=True)
class MockAnswerGenerator:
    answer: str | None = None
    name: str = "mock-generator"
    version: str = "v1"

    def generate(
        self,
        *,
        ticket_text: str,
        context: Sequence[str],
    ) -> str:
        if self.answer is not None:
            return self.answer
        if not context:
            return "NEED_HUMAN_REVIEW"
        return context[0]
