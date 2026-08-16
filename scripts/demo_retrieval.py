from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from support_ai.adapters.retrieval import TfidfKnowledgeBaseRetriever


def main() -> None:
    retriever = TfidfKnowledgeBaseRetriever.from_json(
        PROJECT_ROOT / "data" / "knowledge_base.json"
    )

    for query in (
        "Как поменять пароль?",
        "Приложение после обновления падает",
        "Вчера опять случилось то же самое",
    ):
        print(f"query: {query}")
        for item in retriever.retrieve(query, top_k=3):
            print(
                f"  {item.document_id}: "
                f"score={item.score:.3f}"
            )
        print()


if __name__ == "__main__":
    main()
