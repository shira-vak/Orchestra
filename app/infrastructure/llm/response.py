from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    text: str
    tokens_used: int
