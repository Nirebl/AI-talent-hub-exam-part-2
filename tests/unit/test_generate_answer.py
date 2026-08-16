from support_ai.adapters.in_memory import (
    FailingAnswerGenerator,
    FakeRetriever,
    FakeSafetyChecker,
    InMemoryAnswerRepository,
    InMemoryDecisionRepository,
    InMemoryRetrievalResultRepository,
    InMemoryTicketRepository,
    MockAnswerGenerator,
)
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


def make_llm_ticket() -> Ticket:
    ticket = Ticket(
        text="Как поменять пароль?",
        channel=Channel.WEB,
    )
    ticket.apply_routing(
        prediction=Prediction(TicketCategory.FAQ, 0.96),
        route=HandlingRoute.LLM,
        risk_level=RiskLevel.LOW,
        contains_pii=False,
    )
    return ticket


def build_use_case(*, generator, safety=True):
    ticket_repo = InMemoryTicketRepository()
    decision_repo = InMemoryDecisionRepository()
    answer_repo = InMemoryAnswerRepository()
    retrieval_repo = InMemoryRetrievalResultRepository()

    use_case = GenerateAnswerUseCase(
        ticket_repository=ticket_repo,
        decision_repository=decision_repo,
        answer_repository=answer_repo,
        retrieval_result_repository=retrieval_repo,
        retriever=FakeRetriever(["Пароль меняется в настройках безопасности."]),
        generator=generator,
        safety_checker=FakeSafetyChecker(safety),
    )
    return use_case, ticket_repo, decision_repo, answer_repo


def test_successful_generation_resolves_ticket_and_saves_answer():
    use_case, ticket_repo, _, answer_repo = build_use_case(
        generator=MockAnswerGenerator("Откройте Настройки → Безопасность.")
    )
    ticket = make_llm_ticket()
    ticket_repo.add(ticket)

    answer = use_case.execute(ticket.id)

    assert answer is not None
    assert answer.status is AnswerStatus.SENT
    assert ticket_repo.get(ticket.id).status is TicketStatus.RESOLVED
    assert answer_repo.items == [answer]


def test_unsafe_generated_answer_is_rejected_and_escalated():
    use_case, ticket_repo, decision_repo, answer_repo = build_use_case(
        generator=MockAnswerGenerator("Небезопасный ответ"),
        safety=False,
    )
    ticket = make_llm_ticket()
    ticket_repo.add(ticket)

    answer = use_case.execute(ticket.id)

    assert answer is not None
    assert answer.status is AnswerStatus.REJECTED
    assert ticket_repo.get(ticket.id).route is HandlingRoute.HUMAN
    assert ticket_repo.get(ticket.id).status is TicketStatus.PENDING
    assert decision_repo.items[-1].reason is DecisionReason.UNSAFE_GENERATED_RESPONSE
    assert answer_repo.items[-1] is answer


def test_llm_failure_falls_back_to_human_without_answer():
    use_case, ticket_repo, decision_repo, answer_repo = build_use_case(
        generator=FailingAnswerGenerator()
    )
    ticket = make_llm_ticket()
    ticket_repo.add(ticket)

    answer = use_case.execute(ticket.id)

    assert answer is None
    assert ticket_repo.get(ticket.id).route is HandlingRoute.HUMAN
    assert ticket_repo.get(ticket.id).status is TicketStatus.PENDING
    assert answer_repo.items == []
    assert decision_repo.items[-1].reason is DecisionReason.LLM_UNAVAILABLE


def test_generator_can_abstain():
    use_case, ticket_repo, decision_repo, _ = build_use_case(
        generator=MockAnswerGenerator("NEED_HUMAN_REVIEW")
    )
    ticket = make_llm_ticket()
    ticket_repo.add(ticket)

    answer = use_case.execute(ticket.id)

    assert answer is None
    assert ticket_repo.get(ticket.id).route is HandlingRoute.HUMAN
    assert decision_repo.items[-1].reason is DecisionReason.GENERATOR_ABSTAINED


def test_low_retrieval_score_falls_back_to_human():
    ticket_repo = InMemoryTicketRepository()
    decision_repo = InMemoryDecisionRepository()
    answer_repo = InMemoryAnswerRepository()
    retrieval_repo = InMemoryRetrievalResultRepository()

    use_case = GenerateAnswerUseCase(
        ticket_repository=ticket_repo,
        decision_repository=decision_repo,
        answer_repository=answer_repo,
        retrieval_result_repository=retrieval_repo,
        retriever=FakeRetriever(
            ["Weakly related context"],
            score=0.05,
        ),
        generator=MockAnswerGenerator("This must not be sent"),
        safety_checker=FakeSafetyChecker(True),
        retrieval_score_threshold=0.20,
    )

    ticket = make_llm_ticket()
    ticket_repo.add(ticket)

    answer = use_case.execute(ticket.id)

    assert answer is None
    assert ticket_repo.get(ticket.id).route is HandlingRoute.HUMAN
    assert ticket_repo.get(ticket.id).status is TicketStatus.PENDING
    assert answer_repo.items == []
    assert (
        decision_repo.items[-1].reason
        is DecisionReason.INSUFFICIENT_RETRIEVAL_CONTEXT
    )


def test_retrieval_results_are_audited():
    ticket_repo = InMemoryTicketRepository()
    decision_repo = InMemoryDecisionRepository()
    answer_repo = InMemoryAnswerRepository()
    retrieval_repo = InMemoryRetrievalResultRepository()

    use_case = GenerateAnswerUseCase(
        ticket_repository=ticket_repo,
        decision_repository=decision_repo,
        answer_repository=answer_repo,
        retrieval_result_repository=retrieval_repo,
        retriever=FakeRetriever(
            [
                "Primary context",
                "Secondary context",
            ],
            score=0.9,
        ),
        generator=MockAnswerGenerator("Safe answer"),
        safety_checker=FakeSafetyChecker(True),
    )

    ticket = make_llm_ticket()
    ticket_repo.add(ticket)

    use_case.execute(ticket.id)

    results = retrieval_repo.latest_run_for_ticket(ticket.id)

    assert [item.rank for item in results] == [1, 2]
    assert [item.document_id for item in results] == [
        "fake-0",
        "fake-1",
    ]
    assert all(item.score == 0.9 for item in results)
    assert all(
        item.retriever_name == "fake-retriever"
        for item in results
    )
    assert len({item.retrieval_run_id for item in results}) == 1


def test_redelivered_task_does_not_create_second_answer():
    ticket_repo = InMemoryTicketRepository()
    decision_repo = InMemoryDecisionRepository()
    answer_repo = InMemoryAnswerRepository()
    retrieval_repo = InMemoryRetrievalResultRepository()

    use_case = GenerateAnswerUseCase(
        ticket_repository=ticket_repo,
        decision_repository=decision_repo,
        answer_repository=answer_repo,
        retrieval_result_repository=retrieval_repo,
        retriever=FakeRetriever(["Password reset context"], score=0.9),
        generator=MockAnswerGenerator("Safe answer"),
        safety_checker=FakeSafetyChecker(True),
    )

    ticket = make_llm_ticket()
    ticket_repo.add(ticket)

    first = use_case.execute(ticket.id)
    second = use_case.execute(ticket.id)

    assert first is not None
    assert second is not None
    assert second.id == first.id
    assert len(answer_repo.items) == 1
    assert len(retrieval_repo.items) == 1
