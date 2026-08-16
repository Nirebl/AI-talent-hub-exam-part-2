from support_ai.infrastructure.workers import bootstrap


def test_qwen_worker_warmup_builds_worker_container(monkeypatch):
    called = []

    monkeypatch.setenv("LLM_BACKEND", "qwen")

    from support_ai.infrastructure.workers import dependencies

    monkeypatch.setattr(
        dependencies,
        "get_worker_container",
        lambda: called.append(True),
    )

    bootstrap.warm_generation_worker()

    assert called == [True]


def test_mock_worker_skips_qwen_warmup(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "mock")

    bootstrap.warm_generation_worker()
