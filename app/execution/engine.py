"""Purpose: runs a Plan's parallel_groups via asyncio.gather + a semaphore,
skipping steps whose dependency failed."""

import asyncio
import time

from app.agents.registry import AgentRegistry
from app.enums import StepStatus
from app.execution.context import build_step_input
from app.execution.retry import run_with_retry
from app.infrastructure.db.execution_step_repository import ExecutionStepRepository
from app.infrastructure.db.models import ExecutionStep
from app.planner.schemas.plan import Plan
from app.planner.schemas.plan_step import PlanStep


class ExecutionEngine:
    def __init__(
        self,
        agent_registry: AgentRegistry,
        step_repository: ExecutionStepRepository,
        *,
        max_concurrent_llm_calls: int,
        step_retry_attempts: int,
    ) -> None:
        self._agent_registry = agent_registry
        self._step_repository = step_repository
        self._semaphore = asyncio.Semaphore(max_concurrent_llm_calls)
        self._retry_attempts = step_retry_attempts

    async def run(self, plan: Plan, execution_steps: dict[str, ExecutionStep]) -> dict[str, str]:
        plan_steps_by_id = {step.id: step for step in plan.steps}
        outputs: dict[str, str] = {}
        blocked: set[str] = set()

        for group in plan.parallel_groups:
            await asyncio.gather(
                *(
                    self._run_step(
                        plan_steps_by_id[step_id], execution_steps[step_id], outputs, blocked
                    )
                    for step_id in group
                )
            )

        return outputs

    async def _run_step(
        self,
        plan_step: PlanStep,
        execution_step: ExecutionStep,
        outputs: dict[str, str],
        blocked: set[str],
    ) -> None:
        if any(dep_id in blocked for dep_id in plan_step.dependencies):
            blocked.add(plan_step.id)
            await self._step_repository.update_status(execution_step, status=StepStatus.SKIPPED)
            return

        async with self._semaphore:
            agent = self._agent_registry.get(plan_step.agent)
            input_text = build_step_input(plan_step, outputs)
            await self._step_repository.update_status(execution_step, status=StepStatus.RUNNING)
            started_at = time.monotonic()

            try:
                response = await run_with_retry(
                    lambda: agent.run(input_text), retry_attempts=self._retry_attempts
                )
            except Exception:  # noqa: BLE001 -- exhausted retries; step is marked failed below
                blocked.add(plan_step.id)
                await self._step_repository.update_status(execution_step, status=StepStatus.FAILED)
                return

            elapsed_ms = int((time.monotonic() - started_at) * 1000)
            outputs[plan_step.id] = response.text
            await self._step_repository.update_status(
                execution_step,
                status=StepStatus.COMPLETED,
                output={"text": response.text},
                tokens_used=response.tokens_used,
                execution_time_ms=elapsed_ms,
            )
