from __future__ import annotations

import re


class RegexPiiDetector:
    """Conservative deterministic PII baseline for the PoC.

    Detects common email, phone and payment-card patterns. This is intentionally
    a baseline; production should use a dedicated PII service/model and policy.
    """

    _EMAIL_RE = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    )

    _PHONE_RE = re.compile(
        r"(?<!\d)(?:\+?\d[\s().-]?){10,15}(?!\d)"
    )

    _CARD_CANDIDATE_RE = re.compile(
        r"(?<!\d)(?:\d[\s-]?){13,19}(?!\d)"
    )

    def contains_pii(self, text: str) -> bool:
        if self._EMAIL_RE.search(text):
            return True

        if self._contains_phone(text):
            return True

        if self._contains_valid_card_number(text):
            return True

        return False

    def _contains_phone(self, text: str) -> bool:
        for match in self._PHONE_RE.finditer(text):
            digits = re.sub(r"\D", "", match.group(0))
            if 10 <= len(digits) <= 15:
                return True
        return False

    def _contains_valid_card_number(self, text: str) -> bool:
        for match in self._CARD_CANDIDATE_RE.finditer(text):
            digits = re.sub(r"\D", "", match.group(0))
            if 13 <= len(digits) <= 19 and self._passes_luhn(digits):
                return True
        return False

    @staticmethod
    def _passes_luhn(digits: str) -> bool:
        checksum = 0
        parity = len(digits) % 2

        for index, char in enumerate(digits):
            value = int(char)
            if index % 2 == parity:
                value *= 2
                if value > 9:
                    value -= 9
            checksum += value

        return checksum % 10 == 0
