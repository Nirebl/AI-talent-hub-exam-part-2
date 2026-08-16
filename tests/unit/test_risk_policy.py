from support_ai.domain.entities import Prediction
from support_ai.domain.enums import (
    DecisionReason,
    HandlingRoute,
    RiskLevel,
    TicketCategory,
)
from support_ai.domain.policies import RiskPolicy


def test_safe_high_confidence_ticket_is_routed_to_llm():
    outcome = RiskPolicy().decide(
        prediction=Prediction(TicketCategory.FAQ, 0.95),
        contains_pii=False,
    )

    assert outcome.route is HandlingRoute.LLM
    assert outcome.risk_level is RiskLevel.LOW
    assert outcome.reason is DecisionReason.SAFE_AUTOMATION


def test_high_risk_category_is_routed_to_human_even_with_high_confidence():
    outcome = RiskPolicy().decide(
        prediction=Prediction(TicketCategory.PAYMENT, 0.99),
        contains_pii=False,
    )

    assert outcome.route is HandlingRoute.HUMAN
    assert outcome.risk_level is RiskLevel.HIGH
    assert outcome.reason is DecisionReason.HIGH_RISK_CATEGORY


def test_low_confidence_ticket_is_routed_to_human():
    outcome = RiskPolicy(confidence_threshold=0.80).decide(
        prediction=Prediction(TicketCategory.FAQ, 0.41),
        contains_pii=False,
    )

    assert outcome.route is HandlingRoute.HUMAN
    assert outcome.reason is DecisionReason.LOW_CONFIDENCE


def test_pii_forces_human_route():
    outcome = RiskPolicy().decide(
        prediction=Prediction(TicketCategory.FAQ, 0.99),
        contains_pii=True,
    )

    assert outcome.route is HandlingRoute.HUMAN
    assert outcome.risk_level is RiskLevel.HIGH
    assert outcome.reason is DecisionReason.PII_DETECTED
