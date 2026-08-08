"""Purpose: generates written content for a task's goal — the first (and so
far only) agent implemented, used to prove the submit -> LLM -> persist path
end to end. Research/analysis/code agents land alongside the planner in
Phase 3.
"""

from app.agents.base import BaseAgent
from app.agents.consts import WRITING_AGENT_MAX_TOKENS
from app.agents.prompts import WRITING_AGENT_SYSTEM_PROMPT


class WritingAgent(BaseAgent):
    async def run(self, goal: str) -> str:
        response = await self._llm_client.complete(
            system=WRITING_AGENT_SYSTEM_PROMPT, prompt=goal, max_tokens=WRITING_AGENT_MAX_TOKENS
        )
        return response.text
