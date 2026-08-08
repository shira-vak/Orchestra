"""Purpose: the synthesizer's system prompt + prompt-building — never inline in synthesizer.py."""

from app.planner.schemas.plan import Plan

SYNTHESIS_SYSTEM_PROMPT = (
    "You are a synthesis assistant. Given a goal and the outputs of several "
    "sub-tasks that worked toward it, combine them into one clear, coherent "
    "final answer to the original goal — integrate the information, don't "
    "just concatenate it. Respond with only the finished content."
)


def build_synthesis_prompt(goal: str, plan: Plan, outputs: dict[str, str]) -> str:
    sections = "\n\n".join(
        f"### {step.id} ({step.agent})\n{outputs[step.id]}"
        for step in plan.steps
        if step.id in outputs
    )
    return f"Goal: {goal}\n\nSub-task outputs:\n{sections}"
