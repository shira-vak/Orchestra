"""Purpose: verifies the task submission API end to end — submitting a task
persists it, runs it through the (faked) writing agent, and the result can
be read back; a missing task returns 404.
"""

import httpx

from app.enums import TaskStatus

MOCK_GOAL = "Write a haiku about databases"


async def test_create_task_runs_writing_agent_and_returns_completed_task(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post("/tasks", json={"goal": MOCK_GOAL})

    assert response.status_code == 201
    body = response.json()
    assert body["goal"] == MOCK_GOAL
    assert body["status"] == TaskStatus.COMPLETED
    assert body["result"] == "fake response"
    assert body["id"].startswith("task_")


async def test_create_task_rejects_empty_goal(client: httpx.AsyncClient) -> None:
    response = await client.post("/tasks", json={"goal": ""})

    assert response.status_code == 422


async def test_get_task_returns_persisted_task(client: httpx.AsyncClient) -> None:
    create_response = await client.post("/tasks", json={"goal": MOCK_GOAL})
    task_id = create_response.json()["id"]

    response = await client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["id"] == task_id


async def test_get_task_missing_id_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.get("/tasks/task_doesnotexist")

    assert response.status_code == 404
