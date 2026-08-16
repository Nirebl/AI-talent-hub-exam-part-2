from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from support_ai.adapters.persistence.repositories import (
    SqlAlchemyAnswerRepository,
    SqlAlchemyDecisionRepository,
    SqlAlchemyTicketRepository,
)
from support_ai.adapters.persistence.sqlalchemy_models import (
    AnswerModel,
    Base,
    DecisionModel,
)
from support_ai.domain.entities import Answer, Decision, Prediction, Ticket
from support_ai.domain.enums import (
    AnswerSource,
    AnswerStatus,
    Channel,
    DecisionReason,
    HandlingRoute,
    RiskLevel,
    TicketCategory,
    TicketStatus,
)


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def make_ticket() -> Ticket:
    ticket = Ticket(
        external_id="email-1",
        user_id="user-1",
        channel=Channel.EMAIL,
        text="Как поменять пароль?",
        metadata={
            "language": "ru",
            "client": "web",
        },
    )
    ticket.apply_routing(
        prediction=Prediction(TicketCategory.FAQ, 0.95),
        route=HandlingRoute.LLM,
        risk_level=RiskLevel.LOW,
        contains_pii=False,
    )
    return ticket


def test_ticket_repository_roundtrip():
    session = make_session()
    repository = SqlAlchemyTicketRepository(session)
    ticket = make_ticket()

    repository.add(ticket)
    session.commit()
    session.expunge_all()

    loaded = repository.get(ticket.id)

    assert loaded.id == ticket.id
    assert loaded.external_id == "email-1"
    assert loaded.channel is Channel.EMAIL
    assert loaded.text == "Как поменять пароль?"
    assert loaded.route is HandlingRoute.LLM
    assert loaded.category is TicketCategory.FAQ
    assert loaded.category_confidence == 0.95
    assert loaded.metadata == {
        "language": "ru",
        "client": "web",
    }


def test_ticket_repository_persists_state_transition():
    session = make_session()
    repository = SqlAlchemyTicketRepository(session)
    ticket = make_ticket()
    repository.add(ticket)

    ticket.mark_processing()
    repository.save(ticket)
    session.commit()
    session.expunge_all()

    loaded = repository.get(ticket.id)

    assert loaded.status is TicketStatus.PROCESSING


def test_decision_repository_persists_audit_record():
    session = make_session()
    ticket_repository = SqlAlchemyTicketRepository(session)
    decision_repository = SqlAlchemyDecisionRepository(session)
    ticket = make_ticket()
    ticket_repository.add(ticket)

    decision = Decision(
        ticket_id=ticket.id,
        category=TicketCategory.FAQ,
        confidence=0.95,
        risk_level=RiskLevel.LOW,
        route=HandlingRoute.LLM,
        reason=DecisionReason.SAFE_AUTOMATION,
        classifier_name="test-classifier",
        classifier_version="v1",
        policy_version="v1",
    )

    decision_repository.add(decision)
    session.commit()

    row = session.scalar(
        select(DecisionModel).where(DecisionModel.id == decision.id)
    )

    assert row is not None
    assert row.ticket_id == ticket.id
    assert row.reason == "safe_automation"
    assert row.classifier_version == "v1"


def test_answer_repository_persists_llm_answer():
    session = make_session()
    ticket_repository = SqlAlchemyTicketRepository(session)
    answer_repository = SqlAlchemyAnswerRepository(session)
    ticket = make_ticket()
    ticket_repository.add(ticket)

    answer = Answer(
        ticket_id=ticket.id,
        text="Open Settings and change your password.",
        source=AnswerSource.LLM,
        status=AnswerStatus.SENT,
        model_name="qwen",
        model_version="test",
    )

    answer_repository.add(answer)
    session.commit()

    row = session.scalar(
        select(AnswerModel).where(AnswerModel.id == answer.id)
    )

    assert row is not None
    assert row.ticket_id == ticket.id
    assert row.source == "llm"
    assert row.status == "sent"
