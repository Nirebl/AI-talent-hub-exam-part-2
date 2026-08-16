from enum import StrEnum


class Channel(StrEnum):
    CHAT = "chat"
    EMAIL = "email"
    WEB = "web"
    MOBILE = "mobile"


class TicketStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    FAILED = "failed"


class HandlingRoute(StrEnum):
    HUMAN = "human"
    LLM = "llm"


class RiskLevel(StrEnum):
    LOW = "low"
    HIGH = "high"


class TicketCategory(StrEnum):
    ACCOUNT = "account"
    PAYMENT = "payment"
    REFUND = "refund"
    TECHNICAL = "technical"
    SECURITY = "security"
    FAQ = "faq"
    OTHER = "other"


class DecisionReason(StrEnum):
    SAFE_AUTOMATION = "safe_automation"
    HIGH_RISK_CATEGORY = "high_risk_category"
    LOW_CONFIDENCE = "low_confidence"
    PII_DETECTED = "pii_detected"
    LLM_UNAVAILABLE = "llm_unavailable"
    UNSAFE_GENERATED_RESPONSE = "unsafe_generated_response"
    GENERATOR_ABSTAINED = "generator_abstained"
    INSUFFICIENT_RETRIEVAL_CONTEXT = "insufficient_retrieval_context"


class AnswerSource(StrEnum):
    HUMAN = "human"
    LLM = "llm"


class AnswerStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    REJECTED = "rejected"


class ClientPlatform(StrEnum):
    WEB = "web"
    IOS = "ios"
    ANDROID = "android"
    DESKTOP = "desktop"
    UNKNOWN = "unknown"


class LanguageCode(StrEnum):
    RU = "ru"
    EN = "en"
    UNKNOWN = "unknown"
