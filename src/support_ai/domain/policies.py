from dataclasses import dataclass

from .entities import Prediction
from .enums import (
    DecisionReason,
    HandlingRoute,
    RiskLevel,
    TicketCategory,
)


@dataclass(frozen=True, slots=True)
class RoutingOutcome:
    route: HandlingRoute
    risk_level: RiskLevel
    reason: DecisionReason


@dataclass(frozen=True, slots=True)
class RiskPolicy:
    confidence_threshold: float = 0.80
    policy_version: str = "v1"

    HIGH_RISK_CATEGORIES = frozenset(
        {
            TicketCategory.PAYMENT,
            TicketCategory.REFUND,
            TicketCategory.SECURITY,
        }
    )

    def decide(
        self,
        *,
        prediction: Prediction,
        contains_pii: bool,
    ) -> RoutingOutcome:
        if contains_pii:
            return RoutingOutcome(
                route=HandlingRoute.HUMAN,
                risk_level=RiskLevel.HIGH,
                reason=DecisionReason.PII_DETECTED,
            )

        if prediction.category in self.HIGH_RISK_CATEGORIES:
            return RoutingOutcome(
                route=HandlingRoute.HUMAN,
                risk_level=RiskLevel.HIGH,
                reason=DecisionReason.HIGH_RISK_CATEGORY,
            )

        if prediction.confidence < self.confidence_threshold:
            return RoutingOutcome(
                route=HandlingRoute.HUMAN,
                risk_level=RiskLevel.LOW,
                reason=DecisionReason.LOW_CONFIDENCE,
            )

        return RoutingOutcome(
            route=HandlingRoute.LLM,
            risk_level=RiskLevel.LOW,
            reason=DecisionReason.SAFE_AUTOMATION,
        )
