"""Purpose: verifies the synthesizer combines multi-step outputs via one LLM call (but skips
that call for a single-step plan), and always appends provenance for every step, completed or not.
"""

from app.infrastructure.llm.response import LLMResponse
from app.planner.schemas.plan import Plan
from app.planner.schemas.plan_step import PlanStep
from app.synthesis.synthesizer import Synthesizer
from tests.conftest import MockLLMClient

MOCK_GOAL = "Research a topic and write a summary"

SINGLE_STEP_PLAN = Plan(
    steps=[PlanStep(id="step_1", agent="writing", action="write", input="x", dependencies=[])],
    parallel_groups=[["step_1"]],
)

TWO_STEP_PLAN = Plan(
    steps=[
        PlanStep(id="step_1", agent="research", action="research", input="x", dependencies=[]),
        PlanStep(id="step_2", agent="writing", action="write", input="y", dependencies=["step_1"]),
    ],
    parallel_groups=[["step_1"], ["step_2"]],
)


async def test_synthesize_skips_llm_call_for_single_step_plan() -> None:
    mock_llm_client = MockLLMClient()
    outputs = {"step_1": "the only output"}

    result = await Synthesizer(mock_llm_client).synthesize(
        goal=MOCK_GOAL, plan=SINGLE_STEP_PLAN, outputs=outputs
    )

    assert result.startswith("the only output")
    assert mock_llm_client.calls == []


async def test_synthesize_combines_multiple_step_outputs_via_one_llm_call() -> None:
    mock_llm_client = MockLLMClient(
        default_response=LLMResponse(text="combined answer", tokens_used=20)
    )
    outputs = {"step_1": "research findings", "step_2": "final summary"}

    result = await Synthesizer(mock_llm_client).synthesize(
        goal=MOCK_GOAL, plan=TWO_STEP_PLAN, outputs=outputs
    )

    assert result.startswith("combined answer")
    assert len(mock_llm_client.calls) == 1
    assert "research findings" in mock_llm_client.calls[0]["prompt"]


async def test_synthesize_provenance_notes_steps_that_did_not_complete() -> None:
    mock_llm_client = MockLLMClient(
        default_response=LLMResponse(text="combined answer", tokens_used=20)
    )
    outputs = {"step_1": "research findings"}  # step_2 never completed

    result = await Synthesizer(mock_llm_client).synthesize(
        goal=MOCK_GOAL, plan=TWO_STEP_PLAN, outputs=outputs
    )

    assert "step_1 (research): research — completed" in result
    assert "step_2 (writing): write — did not complete" in result
