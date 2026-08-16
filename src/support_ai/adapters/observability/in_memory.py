from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True, slots=True)
class MetricSummary:
    count: int
    average_ms: float
    max_ms: float
    latest_ms: float


class InMemoryMetricsRecorder:
    def __init__(self, *, max_samples_per_metric: int = 1000) -> None:
        if max_samples_per_metric <= 0:
            raise ValueError("max_samples_per_metric must be positive")

        self._max_samples = max_samples_per_metric
        self._observations: dict[str, list[float]] = defaultdict(list)
        self._counters: dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def observe(self, name: str, value_ms: float) -> None:
        with self._lock:
            values = self._observations[name]
            values.append(float(value_ms))
            if len(values) > self._max_samples:
                del values[: len(values) - self._max_samples]

    def increment(self, name: str) -> None:
        with self._lock:
            self._counters[name] += 1

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            timings = {
                name: self._summarize(values)
                for name, values in sorted(self._observations.items())
                if values
            }
            counters = dict(sorted(self._counters.items()))

        return {
            "timings": {
                name: {
                    "count": summary.count,
                    "average_ms": summary.average_ms,
                    "max_ms": summary.max_ms,
                    "latest_ms": summary.latest_ms,
                }
                for name, summary in timings.items()
            },
            "counters": counters,
        }

    @staticmethod
    def _summarize(values: list[float]) -> MetricSummary:
        return MetricSummary(
            count=len(values),
            average_ms=round(sum(values) / len(values), 3),
            max_ms=round(max(values), 3),
            latest_ms=round(values[-1], 3),
        )
