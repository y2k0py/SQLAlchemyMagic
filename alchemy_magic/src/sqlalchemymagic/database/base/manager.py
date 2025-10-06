from typing import Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

T = TypeVar('T')

class DBManager:

    def __init__(self, session: AsyncSession | Session):
        self.session = session
        self._models = {}

    def __getattr__(self, name: str):
        """Позволяет обращаться к моделям как к атрибутам"""
        if name in self._models:
            return self._models[name]
        return None

    def register_model(self, model_class: Type[T], name: str | None = None) -> Type[T]:
        """Регистрирует модель"""
        model_name = name or model_class.__name__.lower()
        bound_model = model_class.with_session(self.session)
        self._models[model_name] = bound_model
        return bound_model

    def model(self, model_class: Type[T]) -> Type[T]:
        """Возвращает модель с привязанной сессией"""
        return model_class.with_session(self.session)