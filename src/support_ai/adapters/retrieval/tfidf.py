from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from support_ai.application.models import RetrievedDocument


@dataclass(frozen=True, slots=True)
class KnowledgeBaseDocument:
    document_id: str
    text: str


class TfidfKnowledgeBaseRetriever:
    name = "tfidf-knowledge-base-retriever"
    version = "v2"

    def __init__(
        self,
        documents: list[KnowledgeBaseDocument],
    ) -> None:
        if not documents:
            raise ValueError("knowledge base must not be empty")

        self._documents = documents
        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self._matrix = self._vectorizer.fit_transform(
            document.text for document in documents
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "TfidfKnowledgeBaseRetriever":
        path = Path(path)
        payload = json.loads(path.read_text(encoding="utf-8"))

        documents = [
            KnowledgeBaseDocument(
                document_id=item["id"],
                text=item["text"],
            )
            for item in payload
        ]
        return cls(documents)

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 3,
    ) -> list[RetrievedDocument]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        query = query.strip()
        if not query:
            return []

        query_vector = self._vectorizer.transform([query])
        scores = cosine_similarity(
            query_vector,
            self._matrix,
        )[0]

        ranked_indices = scores.argsort()[::-1][:top_k]

        return [
            RetrievedDocument(
                document_id=self._documents[index].document_id,
                text=self._documents[index].text,
                score=float(scores[index]),
            )
            for index in ranked_indices
            if scores[index] > 0.0
        ]
