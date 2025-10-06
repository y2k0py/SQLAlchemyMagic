from typing import Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

T = TypeVar('T')

class SessionMixin:
    """Миксин для моделей SQLAlchemy с автоматической передачей сессии"""

    _session: Session | AsyncSession | None = None

    def bind_session(self, session: Session | AsyncSession):
        """Привязывает сессию к экземпляру модели"""
        self._session = session
        return self

    @classmethod
    def with_session(cls: Type[T], session: Session | AsyncSession) -> T:
        """Создает прокси для класса с привязанной сессией"""

        class SessionBoundModel(cls):
            pass

        SessionBoundModel._session = session
        return SessionBoundModel