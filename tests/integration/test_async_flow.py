from support_ai.adapters.in_memory import (
    FakeClassifier,
    FakeGenerationQueue,
    FakePiiDetector,
    InMemoryAnswerRepository,
    InMemoryDecisionRepository,
    InMemoryTicketRepository,
)
from support_ai.application.use_cases.process_ticket import ProcessTicketUseCase
from support_ai.domain.enums import (
    Channel,
    HandlingRoute,
    TicketCategory,
    TicketStatus,
)
from support_ai.domain.policies import RiskPolicy
from support_ai.infrastructure.workers.dependencies import WorkerContainer
from support_ai.infrastructure.workers.runner import run_generate_answer


def test_safe_ticket_can_flow_from_routing_to_worker_generation():
    ticket_repository = InMemoryTicketRepository()
    decision_repository = InMemoryDecisionRepository()
    answer_repository = InMemoryAnswerRepository()
    queue = FakeGenerationQueue()

    process_ticket = ProcessTicketUseCase(
        classifier=FakeClassifier(TicketCategory.FAQ, 0.96),
        pii_detector=FakePiiDetector(False),
        risk_policy=RiskPolicy(),
        ticket_repository=ticket_repository,
        decision_repository=decision_repository,
        generation_queue=queue,
    )

    result = process_ticket.execute(
        external_id="web-1",
        channel=Channel.WEB,
        text="Как поменять пароль?",
        user_id="user-1",
        metadata={
            "language": "ru",
            "client": "web",
        },
    )

    assert result.ticket.route is HandlingRoute.LLM
    assert queue.items == [result.ticket.id]

    worker = WorkerContainer(
        ticket_repository=ticket_repository,
        decision_repository=decision_repository,
        answer_repository=answer_repository,
    )

    answer = run_generate_answer(
        ticket_id=str(queue.items[0]),
        use_case=worker.generate_answer_use_case,
    )

    assert answer is not None
    assert ticket_repository.get(result.ticket.id).status is TicketStatus.RESOLVED
    assert answer_repository.items == [answer]
