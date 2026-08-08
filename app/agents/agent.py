from app.infrastructure.llm.client import LLMClient
from app.infrastructure.llm.response import LLMResponse


class Agent:
    def __init__(self, llm_client: LLMClient, *, system_prompt: str, max_tokens: int) -> None:
        self._llm_client = llm_client
        self._system_prompt = system_prompt
        self._max_tokens = max_tokens

    async def run(self, input_text: str) -> LLMResponse:
        return await self._llm_client.complete(
            system=self._system_prompt, prompt=input_text, max_tokens=self._max_tokens
        )
