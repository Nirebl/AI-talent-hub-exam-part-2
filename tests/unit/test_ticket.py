from support_ai.domain.entities import Ticket
from support_ai.domain.enums import Channel


def test_ticket_normalizes_text_and_preserves_canonical_fields():
    ticket = Ticket(
        external_id="email-1",
        channel=Channel.EMAIL,
        text="  У меня проблема с оплатой.  ",
        user_id="user-7",
        metadata={
            "thread_id": "thread-1",
            "language": "ru",
            "client": "web",
        },
    )

    assert ticket.text == "У меня проблема с оплатой."
    assert ticket.classifier_text == "У меня проблема с оплатой."
    assert ticket.external_id == "email-1"
    assert ticket.user_id == "user-7"
    assert ticket.metadata == {
        "thread_id": "thread-1",
        "language": "ru",
        "client": "web",
    }
