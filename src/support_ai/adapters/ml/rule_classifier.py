from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from support_ai.domain.entities import Prediction
from support_ai.domain.enums import TicketCategory


@dataclass(frozen=True, slots=True)
class CategoryRule:
    category: TicketCategory
    phrases: tuple[str, ...]
    keywords: tuple[str, ...]


class RuleBasedTicketClassifier:
    """Deterministic multilingual baseline for the PoC hot path.

    This is intentionally not presented as the target ML model. It gives us a
    reproducible, explainable baseline and a real end-to-end routing path before
    historical labeled data is available.
    """

    name = "rule-based-ticket-classifier"
    version = "v1"

    _RULES = (
        CategoryRule(
            category=TicketCategory.SECURITY,
            phrases=(
                "account hacked",
                "hacked my account",
                "unauthorized login",
                "stolen account",
                "взломали аккаунт",
                "аккаунт взломали",
                "мой аккаунт взломали",
                "украли аккаунт",
                "чужой вход",
                "несанкционированный вход",
            ),
            keywords=(
                "hacked",
                "phishing",
                "security",
                "compromised",
                "взлом",
                "взломали",
                "фишинг",
                "безопасность",
                "украли",
            ),
        ),
        CategoryRule(
            category=TicketCategory.REFUND,
            phrases=(
                "refund money",
                "want a refund",
                "return my money",
                "верните деньги",
                "хочу возврат",
                "оформить возврат",
                "вернуть деньги",
            ),
            keywords=(
                "refund",
                "chargeback",
                "возврат",
                "верните",
                "вернуть",
            ),
        ),
        CategoryRule(
            category=TicketCategory.PAYMENT,
            phrases=(
                "payment failed",
                "card charged",
                "charged twice",
                "unauthorized charge",
                "списали деньги",
                "двойное списание",
                "не проходит оплата",
                "не прошла оплата",
                "оплата не проходит",
            ),
            keywords=(
                "payment",
                "charged",
                "billing",
                "card",
                "оплата",
                "платеж",
                "платёж",
                "списали",
                "карта",
                "карты",
            ),
        ),
        CategoryRule(
            category=TicketCategory.ACCOUNT,
            phrases=(
                "reset password",
                "change password",
                "forgot password",
                "cannot log in",
                "can't log in",
                "поменять пароль",
                "сменить пароль",
                "забыл пароль",
                "не могу войти",
                "изменить email",
                "сменить почту",
            ),
            keywords=(
                "password",
                "login",
                "account",
                "пароль",
                "аккаунт",
                "войти",
                "почту",
                "email",
            ),
        ),
        CategoryRule(
            category=TicketCategory.TECHNICAL,
            phrases=(
                "app crashes",
                "service unavailable",
                "does not load",
                "not working",
                "приложение падает",
                "сервис недоступен",
                "не загружается",
                "не работает приложение",
                "ошибка сервера",
            ),
            keywords=(
                "error",
                "crash",
                "bug",
                "broken",
                "ошибка",
                "баг",
                "падает",
                "зависает",
                "недоступен",
                "не работает",
            ),
        ),
        CategoryRule(
            category=TicketCategory.FAQ,
            phrases=(
                "how do i",
                "where can i",
                "where is",
                "как включить",
                "как отключить",
                "где найти",
                "как пользоваться",
            ),
            keywords=(
                "инструкция",
                "help",
            ),
        ),
    )

    _TOKEN_RE = re.compile(r"[a-zа-яё0-9_]+", re.IGNORECASE)

    def predict(self, text: str) -> Prediction:
        normalized = self._normalize(text)
        tokens = Counter(self._TOKEN_RE.findall(normalized))

        scores: dict[TicketCategory, int] = {}

        for rule in self._RULES:
            phrase_hits = sum(
                1 for phrase in rule.phrases if phrase in normalized
            )
            keyword_hits = sum(
                tokens[keyword] for keyword in rule.keywords
            )

            score = phrase_hits * 3 + keyword_hits
            if score:
                scores[rule.category] = score

        if not scores:
            return Prediction(
                category=TicketCategory.OTHER,
                confidence=0.35,
            )

        ranked = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        best_category, best_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0

        confidence = self._confidence(
            best_score=best_score,
            second_score=second_score,
        )
        return Prediction(
            category=best_category,
            confidence=confidence,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.casefold().split())

    @staticmethod
    def _confidence(*, best_score: int, second_score: int) -> float:
        base = 0.62 + min(best_score, 6) * 0.055
        margin = max(best_score - second_score, 0)
        margin_bonus = min(margin, 4) * 0.025
        ambiguity_penalty = 0.10 if second_score and margin <= 1 else 0.0

        return round(
            max(0.0, min(base + margin_bonus - ambiguity_penalty, 0.97)),
            3,
        )
