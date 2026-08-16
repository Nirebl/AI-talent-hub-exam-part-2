from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from support_ai.adapters.llm import build_answer_generator


def main() -> None:
    generator = build_answer_generator()

    answer = generator.generate(
        ticket_text="Как поменять пароль?",
        context=[
            (
                "Password reset. Как поменять пароль: "
                "open Settings > Security and choose Change password."
            )
        ],
    )

    print(f"backend={os.getenv('LLM_BACKEND', 'mock')}")
    print(answer)


if __name__ == "__main__":
    main()
