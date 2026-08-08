"""Purpose: the real `LLMClient` implementation, backed by the Anthropic SDK,
plus the FastAPI dependency that hands it out. Tests override the
`get_llm_client` binding with `FakeLLMClient` instead (see
`tests/conftest.py`) — nothing else in the app imports this module directly.
"""

from anthropic import AsyncAnthropic

from app.config import get_settings
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.llm.response import LLMResponse


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


def get_llm_client() -> LLMClient:
    """FastAPI dependency for the real client. Tests override this binding
    with FakeLLMClient (see tests/conftest.py) instead of monkeypatching.
    """
    return AnthropicClient()
