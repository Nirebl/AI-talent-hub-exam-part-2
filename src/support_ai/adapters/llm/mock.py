from dataclasses import dataclass
from typing import Sequence


@dataclass(slots=True)
class MockAnswerGenerator:
    answer: str = (
        "Open Settings > Security and choose the password reset option."
    )
    name: str = "mock-generator"
    version: str = "v1"

    def generate(
        self,
        *,
        ticket_text: str,
        context: Sequence[str],
    ) -> str:
        return self.answer
