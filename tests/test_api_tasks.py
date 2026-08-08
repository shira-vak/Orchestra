"""Purpose: verifies the task submission API end to end — plan, execute, read back; 422/404 paths"""

import httpx

from app.enums import TaskStatus
from app.infrastructure.llm.response import LLMResponse
from tests.conftest import MockLLMClient
from tests.consts import MOCK_SINGLE_STEP_PLAN_JSON

MOCK_GOAL = "Write a haiku about databases"


async def test_create_task_plans_and_executes_and_returns_completed_task(
    client: httpx.AsyncClient, mock_llm_client: MockLLMClient
) -> None:
    mock_llm_client.default_response = LLMResponse(text=MOCK_SINGLE_STEP_PLAN_JSON, tokens_used=15)

    response = await client.post("/tasks", json={"goal": MOCK_GOAL})

    assert response.status_code == 201
    body = response.json()
    assert body["goal"] == MOCK_GOAL
    assert body["status"] == TaskStatus.COMPLETED
    assert body["result"]
    assert body["id"].startswith("task_")


async def test_create_task_returns_422_when_planner_never_produces_a_valid_plan(
    client: httpx.AsyncClient, mock_llm_client: MockLLMClient
) -> None:
    mock_llm_client.default_response = LLMResponse(text="not a plan", tokens_used=5)

    response = await client.post("/tasks", json={"goal": MOCK_GOAL})

    assert response.status_code == 422


async def test_create_task_rejects_empty_goal(client: httpx.AsyncClient) -> None:
    response = await client.post("/tasks", json={"goal": ""})

    assert response.status_code == 422


async def test_get_task_returns_persisted_task(
    client: httpx.AsyncClient, mock_llm_client: MockLLMClient
) -> None:
    mock_llm_client.default_response = LLMResponse(text=MOCK_SINGLE_STEP_PLAN_JSON, tokens_used=15)

    create_response = await client.post("/tasks", json={"goal": MOCK_GOAL})
    task_id = create_response.json()["id"]

    response = await client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["id"] == task_id


async def test_get_task_missing_id_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.get("/tasks/task_doesnotexist")

    assert response.status_code == 404
