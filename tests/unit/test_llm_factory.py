import pytest

from support_ai.adapters.llm.factory import build_answer_generator
from support_ai.adapters.llm.mock import MockAnswerGenerator


def test_mock_is_default_llm_backend(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)

    generator = build_answer_generator()

    assert isinstance(generator, MockAnswerGenerator)


def test_unknown_llm_backend_is_rejected():
    with pytest.raises(ValueError, match="Unsupported LLM backend"):
        build_answer_generator("unknown")
