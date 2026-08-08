"""Purpose: the return shape of every LLM call — text plus how many tokens
it cost. Kept separate from the `LLMClient` interface so both the interface
and its implementations can import it without a circular dependency.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    text: str
    tokens_used: int
