"""Purpose: FastAPI application entry point — creates the `app` object
Uvicorn serves (see Dockerfile's CMD) and mounts routers/health checks.
Currently only `/health`; task/agent routers land in Phase 2.
"""

from fastapi import FastAPI

app = FastAPI(title="Orchestra", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness check used by docker-compose's healthcheck and, later, by
    any deployment platform's readiness probe. Deliberately has no
    dependencies (no DB call) so it reflects "is the process up", not
    "is the database reachable" — those are different failure modes.
    """
    return {"status": "ok"}
