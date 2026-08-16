from support_ai.adapters.ml import RegexPiiDetector


def test_email_is_detected_as_pii():
    detector = RegexPiiDetector()

    assert detector.contains_pii("Напишите мне на user@example.com")


def test_phone_is_detected_as_pii():
    detector = RegexPiiDetector()

    assert detector.contains_pii("Мой номер +7 999 123-45-67")


def test_valid_card_number_is_detected_as_pii():
    detector = RegexPiiDetector()

    assert detector.contains_pii("Card: 4111 1111 1111 1111")


def test_regular_support_text_is_not_pii():
    detector = RegexPiiDetector()

    assert not detector.contains_pii("Как поменять пароль?")
