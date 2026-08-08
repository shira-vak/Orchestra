"""Combines a plan's step outputs into one final result — an LLM synthesis call
(skipped for a single-step plan) plus a deterministic provenance footer."""

from app.infrastructure.llm.client import LLMClient
from app.planner.schemas.plan import Plan
from app.synthesis.consts import SYNTHESIS_MAX_TOKENS
from app.synthesis.prompts import SYNTHESIS_SYSTEM_PROMPT, build_synthesis_prompt


class Synthesizer:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def synthesize(self, *, goal: str, plan: Plan, outputs: dict[str, str]) -> str:
        body = await self._compose_body(goal, plan, outputs)
        return f"{body}\n\n{_build_provenance(plan, outputs)}"

    async def _compose_body(self, goal: str, plan: Plan, outputs: dict[str, str]) -> str:
        if len(outputs) == 1:
            return next(iter(outputs.values()))

        response = await self._llm_client.complete(
            system=SYNTHESIS_SYSTEM_PROMPT,
            prompt=build_synthesis_prompt(goal, plan, outputs),
            max_tokens=SYNTHESIS_MAX_TOKENS,
        )
        return response.text


def _build_provenance(plan: Plan, outputs: dict[str, str]) -> str:
    lines = ["## Sources"]
    for step in plan.steps:
        outcome = "completed" if step.id in outputs else "did not complete"
        lines.append(f"- {step.id} ({step.agent}): {step.action} — {outcome}")
    return "\n".join(lines)
