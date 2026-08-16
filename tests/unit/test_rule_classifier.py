from support_ai.adapters.ml import RuleBasedTicketClassifier
from support_ai.domain.enums import TicketCategory


def test_password_reset_is_classified_as_account_with_high_confidence():
    classifier = RuleBasedTicketClassifier()

    prediction = classifier.predict("Как поменять пароль?")

    assert prediction.category is TicketCategory.ACCOUNT
    assert prediction.confidence >= 0.80


def test_unauthorized_charge_is_classified_as_payment():
    classifier = RuleBasedTicketClassifier()

    prediction = classifier.predict(
        "С моей карты списали деньги, я не совершал эту операцию"
    )

    assert prediction.category is TicketCategory.PAYMENT
    assert prediction.confidence >= 0.80


def test_hacked_account_is_classified_as_security():
    classifier = RuleBasedTicketClassifier()

    prediction = classifier.predict("Кажется, мой аккаунт взломали")

    assert prediction.category is TicketCategory.SECURITY
    assert prediction.confidence >= 0.80


def test_technical_failure_is_classified_as_technical():
    classifier = RuleBasedTicketClassifier()

    prediction = classifier.predict("После обновления приложение падает")

    assert prediction.category is TicketCategory.TECHNICAL
    assert prediction.confidence >= 0.80


def test_unknown_ticket_abstains_with_low_confidence():
    classifier = RuleBasedTicketClassifier()

    prediction = classifier.predict("Вчера опять было как тогда")

    assert prediction.category is TicketCategory.OTHER
    assert prediction.confidence < 0.80


def test_account_registration_is_classified_as_account_with_high_confidence():
    classifier = RuleBasedTicketClassifier()

    prediction = classifier.predict("Как создать аккаунт?")

    assert prediction.category is TicketCategory.ACCOUNT
    assert prediction.confidence >= 0.80
