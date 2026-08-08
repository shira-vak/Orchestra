from abc import ABC, abstractmethod

from app.infrastructure.llm.response import LLMResponse


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, *, system: str, prompt: str, max_tokens: int) -> LLMResponse:
        raise NotImplementedError
