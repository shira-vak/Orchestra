from collections.abc import Awaitable, Callable

from app.infrastructure.llm.response import LLMResponse


async def run_with_retry(
    action: Callable[[], Awaitable[LLMResponse]], *, retry_attempts: int
) -> LLMResponse:
    last_error: Exception = RuntimeError("run_with_retry called with no attempts")
    for _ in range(retry_attempts + 1):
        try:
            return await action()
        except Exception as exc:  # noqa: BLE001 -- any agent/LLM failure is retryable here
            last_error = exc
    raise last_error
