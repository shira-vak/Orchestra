"""Purpose: FastAPI entry point — creates `app`, mounts routers, maps exceptions to HTTP."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.agents_router import router as agents_router
from app.api.tasks_router import router as tasks_router
from app.exceptions import InvalidPlanError, InvalidTaskStateError, TaskNotFoundError

app = FastAPI(title="Orchestra", version="0.1.0")
app.include_router(tasks_router)
app.include_router(agents_router)


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InvalidPlanError)
async def invalid_plan_handler(request: Request, exc: InvalidPlanError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(InvalidTaskStateError)
async def invalid_task_state_handler(request: Request, exc: InvalidTaskStateError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness check — no DB call, so it reflects "process up," not "DB reachable"."""
    return {"status": "ok"}
