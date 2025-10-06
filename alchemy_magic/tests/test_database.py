import pytest

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from alchemy_magic.src.sqlalchemymagic.database.base.init import InitMagic
from alchemy_magic.src.sqlalchemymagic.database.base.manager import DBManager
from alchemy_magic.src.sqlalchemymagic.database.base.mixin import SessionMixin
from alchemy_magic.src.sqlalchemymagic.database.decorators.session import SessionRequired


class DummyModel(SessionMixin):
    pass


class ExplicitNameModel(SessionMixin):
    pass


class SyncExample(SessionMixin):

    @SessionRequired()
    def compute(self, *, session):
        return session


class AsyncExample(SessionMixin):

    @SessionRequired(async_mode=True)
    async def compute(self, *, session):
        return session


def test_bind_session_returns_same_instance_with_bound_session():
    session = object()
    instance = DummyModel()

    assert instance._session is None

    result = instance.bind_session(session)

    assert result is instance
    assert instance._session is session


def test_with_session_creates_bound_subclass_without_mutating_base():
    session = object()

    BoundModel = DummyModel.with_session(session)

    assert BoundModel is not DummyModel
    assert issubclass(BoundModel, DummyModel)
    assert BoundModel._session is session
    assert DummyModel._session is None

    bound_instance = BoundModel()
    assert bound_instance._session is session


def test_session_required_sync_uses_bound_session_when_missing_kwarg():
    session = object()
    BoundSync = SyncExample.with_session(session)
    instance = BoundSync()

    result = instance.compute()

    assert result is session


def test_session_required_sync_prefers_explicit_session_kwarg():
    default_session = object()
    explicit_session = object()
    BoundSync = SyncExample.with_session(default_session)
    instance = BoundSync()

    result = instance.compute(session=explicit_session)

    assert result is explicit_session


def test_session_required_sync_raises_when_no_session_available():
    instance = SyncExample()

    with pytest.raises(RuntimeError):
        instance.compute()


@pytest.mark.asyncio
async def test_session_required_async_uses_bound_session_when_missing_kwarg():
    session = object()
    BoundAsync = AsyncExample.with_session(session)
    instance = BoundAsync()

    result = await instance.compute()

    assert result is session


@pytest.mark.asyncio
async def test_session_required_async_raises_when_no_session_available():
    instance = AsyncExample()

    with pytest.raises(RuntimeError):
        await instance.compute()


def test_db_manager_registers_and_exposes_models():
    session = object()
    manager = DBManager(session)

    bound = manager.register_model(DummyModel)

    assert bound._session is session
    assert manager.dummymodel is bound
    assert manager.nonexistent is None


def test_db_manager_allows_custom_model_name():
    session = object()
    manager = DBManager(session)

    bound = manager.register_model(ExplicitNameModel, name='custom')

    assert bound._session is session
    assert manager.custom is bound


def test_db_manager_model_method_binds_session_without_registration():
    session = object()
    manager = DBManager(session)

    bound = manager.model(DummyModel)

    assert bound._session is session
    assert 'dummymodel' not in manager._models


def test_init_magic_provides_sync_internals_and_base():
    init = InitMagic(sync_url="sqlite+pysqlite:///:memory:")

    Base = init.base
    assert Base.metadata is init.metadata

    engine = init.sync_engine
    assert engine is init.sync_engine
    assert "sqlite" in str(engine.url)

    sync_factory = init.sync_sessionmaker
    assert sync_factory is init.sync_sessionmaker

    with init.session(commit=False) as session:
        assert isinstance(session, Session)


def test_init_magic_requires_sync_url_for_sync_parts():
    init = InitMagic(async_url="sqlite+aiosqlite:///:memory:")

    with pytest.raises(RuntimeError):
        _ = init.sync_engine

    with pytest.raises(RuntimeError):
        _ = init.sync_sessionmaker

    with pytest.raises(RuntimeError):
        with init.session():
            pass


def test_init_magic_requires_async_url_for_async_engine_and_factory():
    init = InitMagic(sync_url="sqlite+pysqlite:///:memory:")

    with pytest.raises(RuntimeError):
        _ = init.async_engine

    with pytest.raises(RuntimeError):
        _ = init.async_sessionmaker


@pytest.mark.asyncio
async def test_init_magic_provides_async_internals():
    pytest.importorskip("aiosqlite")

    init = InitMagic(async_url="sqlite+aiosqlite:///:memory:")

    engine = init.async_engine
    assert engine is init.async_engine
    assert "sqlite" in str(engine.url)

    async_factory = init.async_sessionmaker
    assert async_factory is init.async_sessionmaker

    async with init.async_session(commit=False) as session:
        assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_init_magic_requires_async_url_for_async_context_manager():
    init = InitMagic(sync_url="sqlite+pysqlite:///:memory:")

    with pytest.raises(RuntimeError):
        async with init.async_session():
            pass


def test_init_magic_requires_at_least_one_url():
    with pytest.raises(ValueError):
        InitMagic()
