from __future__ import annotations

import re
from dataclasses import dataclass

from support_ai.adapters.ml import RegexPiiDetector


@dataclass(frozen=True, slots=True)
class SafetyViolation:
    code: str
    detail: str


class DeterministicSafetyChecker:
    """Conservative post-generation safety baseline.

    The checker is intentionally deterministic and cheap. It protects the
    automatic-send path from obvious unsafe outputs before a human or stronger
    policy/model-based checker is introduced.
    """

    _FINANCIAL_ACTION_PATTERNS = (
        re.compile(
            r"\b(?:i|we)\s+(?:have\s+)?(?:refunded|returned|reimbursed)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:refund|reimbursement|compensation)\s+"
            r"(?:has\s+been|is)\s+(?:approved|issued|processed)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:возврат|компенсация)\s+"
            r"(?:одобрен[ао]?|оформлен[ао]?|выполнен[ао]?)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:я|мы)\s+(?:уже\s+)?"
            r"(?:вернул[иа]?|оформил[иа]?|возместил[иа]?)\s+"
            r"(?:деньги|возврат|компенсацию)\b",
            re.IGNORECASE,
        ),
    )

    _INTERNAL_LEAK_PATTERNS = (
        re.compile(r"\bsystem prompt\b", re.IGNORECASE),
        re.compile(r"\bdeveloper message\b", re.IGNORECASE),
        re.compile(r"\binternal routing\b", re.IGNORECASE),
        re.compile(r"\bconfidence score\b", re.IGNORECASE),
        re.compile(r"\brisk_level\b", re.IGNORECASE),
        re.compile(r"\broute\s*=\s*(?:human|llm)\b", re.IGNORECASE),
        re.compile(r"\bignore previous instructions\b", re.IGNORECASE),
        re.compile(r"\bигнорируй предыдущие инструкции\b", re.IGNORECASE),
    )

    def __init__(
        self,
        *,
        max_length: int = 4_000,
        pii_detector: RegexPiiDetector | None = None,
    ) -> None:
        if max_length <= 0:
            raise ValueError("max_length must be positive")

        self._max_length = max_length
        self._pii_detector = pii_detector or RegexPiiDetector()

    def is_safe(self, text: str) -> bool:
        return not self.violations(text)

    def violations(self, text: str) -> tuple[SafetyViolation, ...]:
        normalized = text.strip()
        violations: list[SafetyViolation] = []

        if not normalized:
            violations.append(
                SafetyViolation(
                    code="empty_answer",
                    detail="generated answer is empty",
                )
            )
            return tuple(violations)

        if normalized == "NEED_HUMAN_REVIEW":
            violations.append(
                SafetyViolation(
                    code="generator_abstained",
                    detail="generator explicitly requested human review",
                )
            )

        if len(normalized) > self._max_length:
            violations.append(
                SafetyViolation(
                    code="answer_too_long",
                    detail=f"answer exceeds {self._max_length} characters",
                )
            )

        if self._pii_detector.contains_pii(normalized):
            violations.append(
                SafetyViolation(
                    code="pii_in_generated_answer",
                    detail="generated answer contains PII-like data",
                )
            )

        if any(
            pattern.search(normalized)
            for pattern in self._FINANCIAL_ACTION_PATTERNS
        ):
            violations.append(
                SafetyViolation(
                    code="unauthorized_financial_action",
                    detail=(
                        "generated answer claims that a refund, reimbursement "
                        "or compensation was executed or approved"
                    ),
                )
            )

        if any(
            pattern.search(normalized)
            for pattern in self._INTERNAL_LEAK_PATTERNS
        ):
            violations.append(
                SafetyViolation(
                    code="internal_instruction_leak",
                    detail=(
                        "generated answer contains internal prompt, routing "
                        "or instruction-like content"
                    ),
                )
            )

        return tuple(violations)
