"""Purpose: the `LLMClient` interface — every LLM call in the app (planner,
all 4 agents, synthesizer) goes through this, never through a provider SDK
directly. That's the seam that lets tests inject a deterministic fake
instead of making real, costly, non-reproducible network calls (see
`tests/conftest.py::FakeLLMClient`).
"""

from abc import ABC, abstractmethod

from app.infrastructure.llm.response import LLMResponse


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, *, system: str, prompt: str, max_tokens: int) -> LLMResponse:
        """Send one prompt, get back text + how many tokens the call cost."""
        raise NotImplementedError
