"""Purpose: LLMClient interface — every LLM call goes through this, never a provider SDK."""

from abc import ABC, abstractmethod

from app.infrastructure.llm.response import LLMResponse


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, *, system: str, prompt: str, max_tokens: int) -> LLMResponse:
        """Send one prompt, get back text + how many tokens the call cost."""
        raise NotImplementedError
