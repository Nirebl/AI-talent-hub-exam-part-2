from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievedDocument:
    document_id: str
    text: str
    score: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("retrieval score must be in [0, 1]")
