"""Purpose: POST /tasks and GET /tasks/{id} — request/response wiring only,
no business logic. All actual work happens in TaskManager.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.writing_agent import WritingAgent
from app.api.schemas.create_task_request import CreateTaskRequest
from app.api.schemas.task_response import TaskResponse
from app.exceptions import TaskNotFoundError
from app.infrastructure.db.models import Task
from app.infrastructure.db.session import get_db_session
from app.infrastructure.db.task_repository import TaskRepository
from app.infrastructure.llm.anthropic_client import get_llm_client
from app.infrastructure.llm.client import LLMClient
from app.tasks.task_manager import TaskManager

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_manager(
    session: AsyncSession = Depends(get_db_session),
    llm_client: LLMClient = Depends(get_llm_client),
) -> TaskManager:
    repository = TaskRepository(session)
    return TaskManager(repository, WritingAgent(llm_client))


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    request: CreateTaskRequest, task_manager: TaskManager = Depends(get_task_manager)
) -> Task:
    return await task_manager.submit(
        goal=request.goal, constraints=request.constraints, output_format=request.output_format
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, task_manager: TaskManager = Depends(get_task_manager)) -> Task:
    task = await task_manager.get(task_id)
    if task is None:
        raise TaskNotFoundError(task_id)
    return task
