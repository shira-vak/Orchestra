from app.infrastructure.llm.response import LLMResponse
from tests.conftest import MockLLMClient


async def test_mock_llm_client_returns_deterministic_response(
    mock_llm_client: MockLLMClient,
) -> None:
    response = await mock_llm_client.complete(system="sys", prompt="hello", max_tokens=100)

    assert isinstance(response, LLMResponse)
    assert response.text == "mock response"
    assert response.tokens_used == 10


async def test_mock_llm_client_records_calls_for_later_assertions(
    mock_llm_client: MockLLMClient,
) -> None:
    await mock_llm_client.complete(system="sys", prompt="what is 2+2", max_tokens=50)

    assert len(mock_llm_client.calls) == 1
    assert mock_llm_client.calls[0]["prompt"] == "what is 2+2"
