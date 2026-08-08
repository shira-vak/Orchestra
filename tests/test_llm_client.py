"""Purpose: verifies `FakeLLMClient` (tests/conftest.py) behaves as every
other test relies on it behaving — deterministic response, calls recorded.
"""

from app.llm.client import LLMResponse
from tests.conftest import FakeLLMClient


async def test_fake_llm_client_returns_deterministic_response(fake_llm_client: FakeLLMClient) -> None:
    response = await fake_llm_client.complete(system="sys", prompt="hello", max_tokens=100)

    assert isinstance(response, LLMResponse)
    assert response.text == "fake response"
    assert response.tokens_used == 10


async def test_fake_llm_client_records_calls_for_later_assertions(
    fake_llm_client: FakeLLMClient,
) -> None:
    await fake_llm_client.complete(system="sys", prompt="what is 2+2", max_tokens=50)

    assert len(fake_llm_client.calls) == 1
    assert fake_llm_client.calls[0]["prompt"] == "what is 2+2"
