"""Purpose: POST /tasks, GET /tasks/{id} — request/response wiring; logic lives in TaskManager."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.registry import AgentRegistry
from app.api.schemas.create_task_request import CreateTaskRequest
from app.api.schemas.task_response import TaskResponse
from app.config import Settings, get_settings
from app.exceptions import TaskNotFoundError
from app.execution.engine import ExecutionEngine
from app.infrastructure.db.execution_plan_repository import ExecutionPlanRepository
from app.infrastructure.db.execution_step_repository import ExecutionStepRepository
from app.infrastructure.db.models import Task
from app.infrastructure.db.session import get_db_session
from app.infrastructure.db.task_repository import TaskRepository
from app.infrastructure.llm.anthropic_client import get_llm_client
from app.infrastructure.llm.client import LLMClient
from app.planner.planner import Planner
from app.tasks.task_manager import TaskManager

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_manager(
    session: AsyncSession = Depends(get_db_session),
    llm_client: LLMClient = Depends(get_llm_client),
    settings: Settings = Depends(get_settings),
) -> TaskManager:
    step_repository = ExecutionStepRepository(session)
    execution_engine = ExecutionEngine(
        AgentRegistry(llm_client),
        step_repository,
        max_concurrent_llm_calls=settings.max_concurrent_llm_calls,
        step_retry_attempts=settings.step_retry_attempts,
    )
    return TaskManager(
        TaskRepository(session),
        ExecutionPlanRepository(session),
        step_repository,
        Planner(llm_client),
        execution_engine,
    )


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
