"""Purpose: LLM call -> parse -> validate a Plan, retried a few times before giving up."""

import json
import re
from typing import Any

from pydantic import ValidationError

from app.exceptions import InvalidPlanError
from app.infrastructure.llm.client import LLMClient
from app.planner.consts import PLANNER_MAX_ATTEMPTS, PLANNER_MAX_TOKENS
from app.planner.prompts import PLANNER_SYSTEM_PROMPT, build_planning_prompt
from app.planner.schemas.plan import Plan
from app.planner.validation import validate_plan

_JSON_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_markdown_fences(text: str) -> str:
    return _JSON_FENCE_PATTERN.sub("", text).strip()


class Planner:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def decompose(self, *, goal: str, constraints: dict[str, Any]) -> Plan:
        last_error: Exception = InvalidPlanError("planner never attempted")

        for _ in range(PLANNER_MAX_ATTEMPTS):
            response = await self._llm_client.complete(
                system=PLANNER_SYSTEM_PROMPT,
                prompt=build_planning_prompt(goal, constraints),
                max_tokens=PLANNER_MAX_TOKENS,
            )
            try:
                plan = Plan.model_validate_json(_strip_markdown_fences(response.text))
                plan.parallel_groups = validate_plan(plan)
                return plan
            except (json.JSONDecodeError, ValidationError, InvalidPlanError) as exc:
                last_error = exc

        raise InvalidPlanError(
            f"planner failed after {PLANNER_MAX_ATTEMPTS} attempts: {last_error}"
        )
