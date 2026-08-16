from support_ai.infrastructure.workers.dependencies import WorkerContainer
from support_ai.infrastructure.workers.runner import run_generate_answer
from support_ai.domain.entities import Prediction, Ticket
from support_ai.domain.enums import (
    Channel,
    HandlingRoute,
    RiskLevel,
    TicketCategory,
    TicketStatus,
)


def make_llm_ticket() -> Ticket:
    ticket = Ticket(
        external_id="web-1",
        channel=Channel.WEB,
        text="Как поменять пароль?",
        user_id="user-1",
        metadata={
            "language": "ru",
            "client": "web",
        },
    )
    ticket.apply_routing(
        prediction=Prediction(
            category=TicketCategory.FAQ,
            confidence=0.96,
        ),
        route=HandlingRoute.LLM,
        risk_level=RiskLevel.LOW,
        contains_pii=False,
    )
    return ticket


def test_worker_runner_executes_generate_answer_use_case():
    container = WorkerContainer()
    ticket = make_llm_ticket()
    container.ticket_repository.add(ticket)

    answer = run_generate_answer(
        ticket_id=str(ticket.id),
        use_case=container.generate_answer_use_case,
    )

    assert answer is not None
    assert answer.ticket_id == ticket.id
    assert container.ticket_repository.get(ticket.id).status is TicketStatus.RESOLVED
    assert len(container.answer_repository.items) == 1


def test_worker_runner_uses_retrieval_generator_and_safety_pipeline():
    container = WorkerContainer()
    ticket = make_llm_ticket()
    container.ticket_repository.add(ticket)

    answer = run_generate_answer(
        ticket_id=str(ticket.id),
        use_case=container.generate_answer_use_case,
    )

    assert answer is not None
    assert "Settings > Security" in answer.text
    assert container.answer_repository.items[0] is answer
