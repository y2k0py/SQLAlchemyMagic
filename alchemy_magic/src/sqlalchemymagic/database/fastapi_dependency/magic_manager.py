from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from alchemy_magic.src.sqlalchemymagic.database.base.manager import DBManager
from alchemy_magic.src.sqlalchemymagic.database.magic_runtime import get_session


async def get_magic_manager(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[DBManager, None]:
    manager = DBManager(session)
    yield manager
