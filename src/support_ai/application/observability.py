from support_ai.application.ports.observability import MetricsRecorder


class NoOpMetricsRecorder:
    def observe(self, name: str, value_ms: float) -> None:
        pass

    def increment(self, name: str) -> None:
        pass


def ensure_metrics(
    metrics: MetricsRecorder | None,
) -> MetricsRecorder:
    return metrics or NoOpMetricsRecorder()
