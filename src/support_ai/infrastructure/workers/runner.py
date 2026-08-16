from uuid import UUID

from support_ai.application.use_cases.generate_answer import GenerateAnswerUseCase


def run_generate_answer(
    *,
    ticket_id: str,
    use_case: GenerateAnswerUseCase,
):
    parsed_ticket_id = UUID(ticket_id)
    return use_case.execute(parsed_ticket_id)
