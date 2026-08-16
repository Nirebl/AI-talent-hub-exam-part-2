from typing import Protocol


class MetricsRecorder(Protocol):
    def observe(self, name: str, value_ms: float) -> None:
        ...

    def increment(self, name: str) -> None:
        ...
