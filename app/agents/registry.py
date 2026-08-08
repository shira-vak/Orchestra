from app.agents.agent import Agent
from app.agents.consts import AGENT_MAX_TOKENS
from app.agents.prompts import (
    ANALYSIS_AGENT_SYSTEM_PROMPT,
    CODE_AGENT_SYSTEM_PROMPT,
    RESEARCH_AGENT_SYSTEM_PROMPT,
    WRITING_AGENT_SYSTEM_PROMPT,
)
from app.enums import AgentName
from app.infrastructure.llm.client import LLMClient


class AgentRegistry:
    def __init__(self, llm_client: LLMClient) -> None:
        self._agents: dict[AgentName, Agent] = {
            AgentName.RESEARCH: Agent(
                llm_client, system_prompt=RESEARCH_AGENT_SYSTEM_PROMPT, max_tokens=AGENT_MAX_TOKENS
            ),
            AgentName.WRITING: Agent(
                llm_client, system_prompt=WRITING_AGENT_SYSTEM_PROMPT, max_tokens=AGENT_MAX_TOKENS
            ),
            AgentName.ANALYSIS: Agent(
                llm_client, system_prompt=ANALYSIS_AGENT_SYSTEM_PROMPT, max_tokens=AGENT_MAX_TOKENS
            ),
            AgentName.CODE: Agent(
                llm_client, system_prompt=CODE_AGENT_SYSTEM_PROMPT, max_tokens=AGENT_MAX_TOKENS
            ),
        }

    def get(self, name: AgentName) -> Agent:
        return self._agents[name]
