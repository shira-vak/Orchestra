"""Purpose: defines the `LLMClient` interface and its real implementation
(`AnthropicClient`), so the rest of the app never imports the Anthropic SDK
directly — see the `LLMClient` docstring below for why that seam matters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from anthropic import AsyncAnthropic

from app.config import get_settings


@dataclass(frozen=True)
class LLMResponse:
    text: str
    tokens_used: int


class LLMClient(ABC):
    """Every LLM call in the app — planner, all 4 agents, synthesizer —
    goes through this interface, never through a provider SDK directly.
    That's the seam that lets tests inject a deterministic fake instead of
    making real, costly, non-reproducible network calls (see
    `tests/conftest.py::FakeLLMClient`).
    """

    @abstractmethod
    async def complete(self, *, system: str, prompt: str, max_tokens: int) -> LLMResponse:
        """Send one prompt, get back text + how many tokens the call cost."""
        raise NotImplementedError


class AnthropicClient(LLMClient):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def complete(self, *, system: str, prompt: str, max_tokens: int) -> LLMResponse:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        return LLMResponse(text=text, tokens_used=tokens_used)
