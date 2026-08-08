"""Purpose: FastAPI application entry point — creates the `app` object
Uvicorn serves (see Dockerfile's CMD), mounts routers, and maps domain
exceptions to HTTP responses in one place.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.agents_router import router as agents_router
from app.api.tasks_router import router as tasks_router
from app.exceptions import TaskNotFoundError

app = FastAPI(title="Orchestra", version="0.1.0")
app.include_router(tasks_router)
app.include_router(agents_router)


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness check used by docker-compose's healthcheck and, later, by
    any deployment platform's readiness probe. Deliberately has no
    dependencies (no DB call) so it reflects "is the process up", not
    "is the database reachable" — those are different failure modes.
    """
    return {"status": "ok"}
