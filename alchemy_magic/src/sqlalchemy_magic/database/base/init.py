from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class InitMagic:
    """Factory for SQLAlchemy primitives bound to sync and async engines."""

    def __init__(
        self,
        *,
        sync_url: str | None = None,
        async_url: str | None = None,
        sync_engine_kwargs: dict[str, Any] | None = None,
        async_engine_kwargs: dict[str, Any] | None = None,
        sync_session_kwargs: dict[str, Any] | None = None,
        async_session_kwargs: dict[str, Any] | None = None,
    ) -> None:
        if not sync_url and not async_url:
            raise ValueError("Provide at least one of sync_url or async_url.")

        self.sync_url = sync_url
        self.async_url = async_url
        self._sync_engine_kwargs = dict(sync_engine_kwargs or {})
        self._async_engine_kwargs = dict(async_engine_kwargs or {})
        self._sync_session_kwargs = dict(sync_session_kwargs or {})
        self._async_session_kwargs = dict(async_session_kwargs or {})

        self._base = self._create_base()
        self._sync_engine: Engine | None = None
        self._async_engine: AsyncEngine | None = None
        self._sync_sessionmaker: sessionmaker[Session] | None = None
        self._async_sessionmaker: async_sessionmaker[AsyncSession] | None = None

    @staticmethod
    def _create_base() -> type[DeclarativeBase]:
        class Base(DeclarativeBase):
            pass

        return Base

    @property
    def base(self) -> type[DeclarativeBase]:
        return self._base

    @property
    def metadata(self):
        return self._base.metadata

    def _require_sync_url(self) -> str:
        if not self.sync_url:
            raise RuntimeError("Synchronous database URL is not configured.")
        return self.sync_url

    def _require_async_url(self) -> str:
        if not self.async_url:
            raise RuntimeError("Asynchronous database URL is not configured.")
        return self.async_url

    @property
    def sync_engine(self) -> Engine:
        if self._sync_engine is None:
            url = self._require_sync_url()
            self._sync_engine = create_engine(url, **self._sync_engine_kwargs)
        return self._sync_engine

    @property
    def async_engine(self) -> AsyncEngine:
        if self._async_engine is None:
            url = self._require_async_url()
            self._async_engine = create_async_engine(url, **self._async_engine_kwargs)
        return self._async_engine

    @property
    def sync_sessionmaker(self) -> sessionmaker[Session]:
        if self._sync_sessionmaker is None:
            engine = self.sync_engine
            self._sync_sessionmaker = sessionmaker(
                engine,
                expire_on_commit=False,
                class_=Session,
                **self._sync_session_kwargs,
            )
        return self._sync_sessionmaker

    @property
    def async_sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        if self._async_sessionmaker is None:
            engine = self.async_engine
            self._async_sessionmaker = async_sessionmaker(
                engine,
                expire_on_commit=False,
                class_=AsyncSession,
                **self._async_session_kwargs,
            )
        return self._async_sessionmaker

    @contextmanager
    def session(self, *, commit: bool = True) -> Iterator[Session]:
        session = self.sync_sessionmaker()
        try:
            yield session
            if commit:
                session.commit()
        except Exception:
            try:
                session.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                session.close()
            except Exception:
                pass

    @asynccontextmanager
    async def async_session(self, *, commit: bool = True) -> AsyncIterator[AsyncSession]:
        session = self.async_sessionmaker()
        try:
            yield session
            if commit:
                await session.commit()
        except Exception:
            try:
                await session.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                await session.close()
            except Exception:
                pass
