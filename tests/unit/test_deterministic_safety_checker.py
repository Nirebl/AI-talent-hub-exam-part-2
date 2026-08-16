from support_ai.adapters.safety import DeterministicSafetyChecker


def test_normal_grounded_support_answer_is_safe():
    checker = DeterministicSafetyChecker()

    assert checker.is_safe(
        "Open Settings > Security and choose Change password."
    )


def test_empty_answer_is_rejected():
    checker = DeterministicSafetyChecker()

    assert not checker.is_safe("   ")
    assert checker.violations("   ")[0].code == "empty_answer"


def test_generated_pii_is_rejected():
    checker = DeterministicSafetyChecker()

    violations = checker.violations(
        "We will contact you at user@example.com."
    )

    assert any(
        item.code == "pii_in_generated_answer"
        for item in violations
    )


def test_unapproved_refund_claim_is_rejected():
    checker = DeterministicSafetyChecker()

    violations = checker.violations(
        "We have refunded the payment to your card."
    )

    assert any(
        item.code == "unauthorized_financial_action"
        for item in violations
    )


def test_russian_refund_claim_is_rejected():
    checker = DeterministicSafetyChecker()

    violations = checker.violations(
        "Возврат оформлен, деньги поступят в течение трех дней."
    )

    assert any(
        item.code == "unauthorized_financial_action"
        for item in violations
    )


def test_internal_prompt_or_routing_leak_is_rejected():
    checker = DeterministicSafetyChecker()

    violations = checker.violations(
        "Internal routing: route=human, confidence score 0.91."
    )

    codes = {item.code for item in violations}
    assert "internal_instruction_leak" in codes


def test_overlong_answer_is_rejected():
    checker = DeterministicSafetyChecker(max_length=20)

    violations = checker.violations(
        "This answer is definitely longer than twenty characters."
    )

    assert any(
        item.code == "answer_too_long"
        for item in violations
    )
