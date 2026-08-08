"""Purpose: verifies the planner turns LLM output into a validated, layered Plan, or retries and
rejects an invalid one (unknown reference, cycle, bad JSON)."""

import json

import pytest

from app.exceptions import InvalidPlanError
from app.infrastructure.llm.response import LLMResponse
from app.planner.consts import PLANNER_MAX_ATTEMPTS
from app.planner.planner import Planner
from tests.conftest import MockLLMClient

MOCK_GOAL = "Research a topic and write a summary"


def _plan_json(*steps: dict[str, object]) -> str:
    return json.dumps({"steps": list(steps)})


def _step(step_id: str, agent: str, input_text: str, dependencies: list[str]) -> dict[str, object]:
    return {
        "id": step_id,
        "agent": agent,
        "action": agent,
        "input": input_text,
        "dependencies": dependencies,
    }


SEQUENTIAL_PLAN_JSON = _plan_json(
    _step("step_1", "research", "topic", []),
    _step("step_2", "writing", "summarize", ["step_1"]),
)

PARALLEL_PLAN_JSON = _plan_json(
    _step("step_1", "research", "topic a", []),
    _step("step_2", "research", "topic b", []),
)

UNKNOWN_REFERENCE_PLAN_JSON = _plan_json(
    _step("step_1", "writing", "x", ["step_does_not_exist"]),
)

CYCLE_PLAN_JSON = _plan_json(
    _step("step_1", "writing", "x", ["step_2"]),
    _step("step_2", "writing", "y", ["step_1"]),
)


async def test_decompose_computes_sequential_parallel_groups() -> None:
    mock_llm_client = MockLLMClient(
        default_response=LLMResponse(text=SEQUENTIAL_PLAN_JSON, tokens_used=10)
    )
    planner = Planner(mock_llm_client)

    plan = await planner.decompose(goal=MOCK_GOAL, constraints={})

    assert plan.parallel_groups == [["step_1"], ["step_2"]]


async def test_decompose_computes_parallel_groups_for_independent_steps() -> None:
    mock_llm_client = MockLLMClient(
        default_response=LLMResponse(text=PARALLEL_PLAN_JSON, tokens_used=10)
    )
    planner = Planner(mock_llm_client)

    plan = await planner.decompose(goal=MOCK_GOAL, constraints={})

    assert plan.parallel_groups == [["step_1", "step_2"]]


async def test_decompose_strips_markdown_fences_around_json() -> None:
    fenced = f"```json\n{SEQUENTIAL_PLAN_JSON}\n```"
    mock_llm_client = MockLLMClient(default_response=LLMResponse(text=fenced, tokens_used=10))
    planner = Planner(mock_llm_client)

    plan = await planner.decompose(goal=MOCK_GOAL, constraints={})

    assert len(plan.steps) == 2


async def test_decompose_retries_then_succeeds_after_malformed_json() -> None:
    mock_llm_client = MockLLMClient(
        responses=[
            LLMResponse(text="not json at all", tokens_used=5),
            LLMResponse(text=SEQUENTIAL_PLAN_JSON, tokens_used=10),
        ]
    )
    planner = Planner(mock_llm_client)

    plan = await planner.decompose(goal=MOCK_GOAL, constraints={})

    assert len(plan.steps) == 2
    assert len(mock_llm_client.calls) == 2


async def test_decompose_raises_invalid_plan_error_for_unknown_step_reference() -> None:
    mock_llm_client = MockLLMClient(
        default_response=LLMResponse(text=UNKNOWN_REFERENCE_PLAN_JSON, tokens_used=10)
    )
    planner = Planner(mock_llm_client)

    with pytest.raises(InvalidPlanError):
        await planner.decompose(goal=MOCK_GOAL, constraints={})

    assert len(mock_llm_client.calls) == PLANNER_MAX_ATTEMPTS


async def test_decompose_raises_invalid_plan_error_for_cycle() -> None:
    mock_llm_client = MockLLMClient(
        default_response=LLMResponse(text=CYCLE_PLAN_JSON, tokens_used=10)
    )
    planner = Planner(mock_llm_client)

    with pytest.raises(InvalidPlanError):
        await planner.decompose(goal=MOCK_GOAL, constraints={})


async def test_decompose_raises_invalid_plan_error_after_exhausting_malformed_json_retries() -> (
    None
):
    mock_llm_client = MockLLMClient(
        default_response=LLMResponse(text="not json at all", tokens_used=5)
    )
    planner = Planner(mock_llm_client)

    with pytest.raises(InvalidPlanError):
        await planner.decompose(goal=MOCK_GOAL, constraints={})

    assert len(mock_llm_client.calls) == PLANNER_MAX_ATTEMPTS
