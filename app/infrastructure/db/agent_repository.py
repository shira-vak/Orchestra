from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Agent


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Agent]:
        result = await self._session.execute(select(Agent))
        return list(result.scalars().all())
