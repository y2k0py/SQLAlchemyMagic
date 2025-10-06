from dataclasses import dataclass
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from .base import InitMagic

_magic_singleton: InitMagic | None = None


def configure_magic(
    *,
    sync_url: str | None = None,
    async_url: str | None = None,
    sync_engine_kwargs: dict | None = None,
    async_engine_kwargs: dict | None = None,
    sync_session_kwargs: dict | None = None,
    async_session_kwargs: dict | None = None,
) -> InitMagic:
    global _magic_singleton
    _magic_singleton = InitMagic(
        sync_url=sync_url,
        async_url=async_url,
        sync_engine_kwargs=sync_engine_kwargs,
        async_engine_kwargs=async_engine_kwargs,
        sync_session_kwargs=sync_session_kwargs,
        async_session_kwargs=async_session_kwargs,
    )
    return _magic_singleton


def get_magic() -> InitMagic:
    if _magic_singleton is None:
        raise RuntimeError("InitMagic is not configured. Call configure_magic() first.")
    return _magic_singleton


async def get_session(magic: InitMagic = Depends(get_magic)) -> AsyncGenerator[AsyncSession, None]:
    async with magic.async_session(commit=False) as session:
        yield session


@dataclass
class MagicScope:
    manager: InitMagic
    session: AsyncSession


async def get_magic_scope(
    magic: InitMagic = Depends(get_magic),
) -> AsyncGenerator[MagicScope, None]:
    async with magic.async_session(commit=False) as session:
        yield MagicScope(manager=magic, session=session)
