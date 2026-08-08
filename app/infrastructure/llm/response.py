"""Purpose: the return shape of every LLM call — text plus tokens used."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    text: str
    tokens_used: int
