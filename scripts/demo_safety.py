from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from support_ai.adapters.safety import DeterministicSafetyChecker


CASES = (
    "Open Settings > Security and choose Change password.",
    "We have refunded the payment to your card.",
    "Contact user@example.com for the next step.",
    "Internal routing: route=human, confidence score 0.91.",
)


def main() -> None:
    checker = DeterministicSafetyChecker()

    for text in CASES:
        violations = checker.violations(text)
        print(text)
        print(
            "safe" if not violations else
            ", ".join(item.code for item in violations)
        )
        print()


if __name__ == "__main__":
    main()
