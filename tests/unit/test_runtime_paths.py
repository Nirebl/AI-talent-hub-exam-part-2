from pathlib import Path

from support_ai.infrastructure.paths import resolve_knowledge_base_path


def test_explicit_knowledge_base_path_has_highest_priority(monkeypatch):
    monkeypatch.setenv(
        "KNOWLEDGE_BASE_PATH",
        "/configured/knowledge_base.json",
    )

    result = resolve_knowledge_base_path(
        "/explicit/knowledge_base.json"
    )

    assert result == Path("/explicit/knowledge_base.json")


def test_configured_knowledge_base_path_is_used(monkeypatch):
    monkeypatch.setenv(
        "KNOWLEDGE_BASE_PATH",
        "/app/data/knowledge_base.json",
    )

    result = resolve_knowledge_base_path()

    assert result == Path("/app/data/knowledge_base.json")


def test_default_knowledge_base_path_uses_current_working_directory(
    monkeypatch,
    tmp_path,
):
    monkeypatch.delenv("KNOWLEDGE_BASE_PATH", raising=False)
    monkeypatch.chdir(tmp_path)

    result = resolve_knowledge_base_path()

    assert result == tmp_path / "data" / "knowledge_base.json"
