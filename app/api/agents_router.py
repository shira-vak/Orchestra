from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.agent_response import AgentResponse
from app.infrastructure.db.agent_repository import AgentRepository
from app.infrastructure.db.models import Agent
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentResponse])
async def list_agents(session: AsyncSession = Depends(get_db_session)) -> list[Agent]:
    return await AgentRepository(session).list_all()
