from support_ai.adapters.retrieval.tfidf import (
    KnowledgeBaseDocument,
    TfidfKnowledgeBaseRetriever,
)


def build_retriever() -> TfidfKnowledgeBaseRetriever:
    return TfidfKnowledgeBaseRetriever(
        [
            KnowledgeBaseDocument(
                document_id="password",
                text="Как поменять пароль. Password reset in Settings Security.",
            ),
            KnowledgeBaseDocument(
                document_id="notifications",
                text="Как отключить уведомления. Notification settings.",
            ),
            KnowledgeBaseDocument(
                document_id="technical",
                text="Приложение падает и не работает. Application troubleshooting.",
            ),
        ]
    )


def test_password_query_returns_password_document_first():
    retriever = build_retriever()

    results = retriever.retrieve("Как поменять пароль?", top_k=2)

    assert results
    assert results[0].document_id == "password"
    assert results[0].score > 0.20


def test_unrelated_query_has_no_useful_match():
    retriever = build_retriever()

    results = retriever.retrieve("Вчера опять случилось то же самое", top_k=3)

    assert results == []


def test_retrieval_results_are_ranked_by_score():
    retriever = build_retriever()

    results = retriever.retrieve("приложение не работает", top_k=3)

    assert results[0].document_id == "technical"
    assert results == sorted(
        results,
        key=lambda item: item.score,
        reverse=True,
    )


def test_technical_query_clears_poc_threshold():
    retriever = TfidfKnowledgeBaseRetriever(
        [
            KnowledgeBaseDocument(
                document_id="technical",
                text=(
                    "Application troubleshooting. "
                    "Если приложение не работает, падает или не загружается."
                ),
            ),
            KnowledgeBaseDocument(
                document_id="password",
                text="Как поменять пароль. Password reset.",
            ),
        ]
    )

    results = retriever.retrieve(
        "Приложение после обновления падает",
        top_k=2,
    )

    assert results[0].document_id == "technical"
    assert results[0].score >= 0.15


def test_registration_query_returns_registration_article(tmp_path):
    path = tmp_path / "knowledge_base.json"
    path.write_text(
        """[
          {
            "id": "account-registration",
            "text": "Как создать аккаунт или зарегистрироваться. Create account and confirm email."
          },
          {
            "id": "account-password-reset",
            "text": "Как поменять пароль. Password reset."
          }
        ]""",
        encoding="utf-8",
    )

    retriever = TfidfKnowledgeBaseRetriever.from_json(path)

    results = retriever.retrieve("Как создать аккаунт?", top_k=2)

    assert results
    assert results[0].document_id == "account-registration"
    assert results[0].score >= 0.15
