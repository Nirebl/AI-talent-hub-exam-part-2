from support_ai.adapters.in_memory import (
    FakeRetriever,
    InMemoryAnswerRepository,
    InMemoryDecisionRepository,
    InMemoryTicketRepository,
    MockAnswerGenerator,
)
from support_ai.adapters.safety import DeterministicSafetyChecker
from support_ai.application.use_cases.generate_answer import GenerateAnswerUseCase
from support_ai.domain.entities import Prediction, Ticket
from support_ai.domain.enums import (
    AnswerStatus,
    Channel,
    DecisionReason,
    HandlingRoute,
    RiskLevel,
    TicketCategory,
    TicketStatus,
)


def test_real_safety_checker_blocks_financial_claim_and_escalates():
    ticket_repository = InMemoryTicketRepository()
    decision_repository = InMemoryDecisionRepository()
    answer_repository = InMemoryAnswerRepository()

    ticket = Ticket(
        channel=Channel.WEB,
        text="Как поменять пароль?",
    )
    ticket.apply_routing(
        prediction=Prediction(
            category=TicketCategory.ACCOUNT,
            confidence=0.95,
        ),
        route=HandlingRoute.LLM,
        risk_level=RiskLevel.LOW,
        contains_pii=False,
    )
    ticket_repository.add(ticket)

    use_case = GenerateAnswerUseCase(
        ticket_repository=ticket_repository,
        decision_repository=decision_repository,
        answer_repository=answer_repository,
        retriever=FakeRetriever(
            ["Password reset is available in Settings > Security."],
            score=0.95,
        ),
        generator=MockAnswerGenerator(
            "We have refunded the payment to your card."
        ),
        safety_checker=DeterministicSafetyChecker(),
        retrieval_score_threshold=0.15,
    )

    answer = use_case.execute(ticket.id)

    assert answer is not None
    assert answer.status is AnswerStatus.REJECTED
    assert ticket_repository.get(ticket.id).route is HandlingRoute.HUMAN
    assert ticket_repository.get(ticket.id).status is TicketStatus.PENDING
    assert (
        decision_repository.items[-1].reason
        is DecisionReason.UNSAFE_GENERATED_RESPONSE
    )
