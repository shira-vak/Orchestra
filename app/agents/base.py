"""Purpose: shared interface every agent implements — one method, `run`,
that takes a goal and returns generated text via the injected LLM client.
Kept to one method deliberately: the planner (Phase 3) will call agents
uniformly regardless of which one it picked, so agents must not leak
provider- or agent-specific extras onto this interface.
"""

from abc import ABC, abstractmethod

from app.infrastructure.llm.client import LLMClient


class BaseAgent(ABC):
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    @abstractmethod
    async def run(self, goal: str) -> str:
        """Produce this agent's output for the given goal."""
        raise NotImplementedError
