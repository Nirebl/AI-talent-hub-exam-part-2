from support_ai.adapters.observability import InMemoryMetricsRecorder


def test_metrics_recorder_aggregates_timings_and_counters():
    metrics = InMemoryMetricsRecorder()

    metrics.observe("routing.total_ms", 10.0)
    metrics.observe("routing.total_ms", 20.0)
    metrics.increment("routing.route.llm")
    metrics.increment("routing.route.llm")

    snapshot = metrics.snapshot()

    assert snapshot["timings"]["routing.total_ms"] == {
        "count": 2,
        "average_ms": 15.0,
        "max_ms": 20.0,
        "latest_ms": 20.0,
    }
    assert snapshot["counters"]["routing.route.llm"] == 2
