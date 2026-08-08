"""Purpose: verifies the task submission API end to end — plan synchronously (422 on
a bad plan), execute in the background, poll to a terminal status, read the result back."""

import httpx

from app.enums import TaskStatus
from app.infrastructure.llm.anthropic_client import get_llm_client
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.llm.response import LLMResponse
from app.main import app
from tests.conftest import MockLLMClient, wait_for_terminal_status
from tests.consts import MOCK_SINGLE_STEP_PLAN_JSON

MOCK_GOAL = "Write a haiku about databases"


class _AuthFailingLLMClient(LLMClient):
    async def complete(self, *, system: str, prompt: str, max_tokens: int) -> LLMResponse:
        raise TypeError("Could not resolve authentication method")


async def test_create_task_plans_synchronously_and_executes_in_background(
    client: httpx.AsyncClient, mock_llm_client: MockLLMClient
) -> None:
    mock_llm_client.default_response = LLMResponse(text=MOCK_SINGLE_STEP_PLAN_JSON, tokens_used=15)

    response = await client.post("/tasks", json={"goal": MOCK_GOAL})

    assert response.status_code == 201
    body = response.json()
    assert body["goal"] == MOCK_GOAL
    assert body["id"].startswith("task_")

    final = await wait_for_terminal_status(client, body["id"])
    assert final["status"] == TaskStatus.COMPLETED
    assert final["result"]


async def test_create_task_returns_422_when_planner_never_produces_a_valid_plan(
    client: httpx.AsyncClient, mock_llm_client: MockLLMClient
) -> None:
    mock_llm_client.default_response = LLMResponse(text="not a plan", tokens_used=5)

    response = await client.post("/tasks", json={"goal": MOCK_GOAL})

    assert response.status_code == 422


async def test_create_task_returns_502_with_detail_when_the_llm_provider_call_fails(
    client: httpx.AsyncClient,
) -> None:
    app.dependency_overrides[get_llm_client] = lambda: _AuthFailingLLMClient()

    response = await client.post("/tasks", json={"goal": MOCK_GOAL})

    assert response.status_code == 502
    assert "Could not resolve authentication method" in response.json()["detail"]


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
    await wait_for_terminal_status(client, task_id)


async def test_get_task_missing_id_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.get("/tasks/task_doesnotexist")

    assert response.status_code == 404


async def test_get_task_result_includes_step_provenance(
    client: httpx.AsyncClient, mock_llm_client: MockLLMClient
) -> None:
    mock_llm_client.default_response = LLMResponse(text=MOCK_SINGLE_STEP_PLAN_JSON, tokens_used=15)

    task_id = (await client.post("/tasks", json={"goal": MOCK_GOAL})).json()["id"]
    await wait_for_terminal_status(client, task_id)

    response = await client.get(f"/tasks/{task_id}/result")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == TaskStatus.COMPLETED
    assert body["result"]
    assert len(body["steps"]) == 1
    assert body["steps"][0]["status"] == "completed"


async def test_get_task_result_missing_id_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.get("/tasks/task_doesnotexist/result")

    assert response.status_code == 404


async def test_cancel_task_marks_it_cancelled(
    client: httpx.AsyncClient, mock_llm_client: MockLLMClient
) -> None:
    mock_llm_client.default_response = LLMResponse(text=MOCK_SINGLE_STEP_PLAN_JSON, tokens_used=15)

    task_id = (await client.post("/tasks", json={"goal": MOCK_GOAL})).json()["id"]

    response = await client.post(f"/tasks/{task_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == TaskStatus.CANCELLED
    # a single-step plan may already finish its one group before cancellation lands
    final = await wait_for_terminal_status(client, task_id)
    assert final["status"] in {TaskStatus.CANCELLED, TaskStatus.COMPLETED}


async def test_cancel_task_missing_id_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.post("/tasks/task_doesnotexist/cancel")

    assert response.status_code == 404


async def test_cancel_already_completed_task_returns_409(
    client: httpx.AsyncClient, mock_llm_client: MockLLMClient
) -> None:
    mock_llm_client.default_response = LLMResponse(text=MOCK_SINGLE_STEP_PLAN_JSON, tokens_used=15)

    task_id = (await client.post("/tasks", json={"goal": MOCK_GOAL})).json()["id"]
    await wait_for_terminal_status(client, task_id)

    response = await client.post(f"/tasks/{task_id}/cancel")

    assert response.status_code == 409
