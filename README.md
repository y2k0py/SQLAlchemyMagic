# SQLAlchemy Magic

SQLAlchemy Magic is a lightweight toolkit that smooths out working with SQLAlchemy in projects that juggle synchronous and asynchronous code, especially FastAPI services. It centralises engine configuration, session lifecycle management, and model helpers so you can focus on your application logic instead of plumbing.

## Features
- Single place to configure both sync and async SQLAlchemy engines and session factories.
- Drop-in context managers for transactional sync and async sessions.
- Model mixin and decorator utilities that inject sessions automatically into your repository methods.
- `DBManager` helper to bind multiple models or repositories to the same session in one shot.
- Ready-to-use FastAPI dependencies for wiring sessions or `DBManager` instances into your routes.

## Requirements
- Python 3.13+
- SQLAlchemy 2.0+
- An async driver that matches your database URL (e.g. `aiosqlite` for SQLite, `asyncpg` for PostgreSQL).

## Installation
Install from PyPI with pip (or your preferred installer):

```bash
pip install sqlalchemy-magic
```

For local development, install with Poetry to pick up the test dependencies:

```bash
poetry install
```

## Quick Start
Configure the library once at application startup, then use the returned `InitMagic` factory to declare models and open sessions.

```python
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from alchemy_magic import configure_magic

magic = configure_magic(
    sync_url="sqlite+pysqlite:///./app.db",
    async_url="sqlite+aiosqlite:///./app.db",
)

Base = magic.base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)

# Create tables using the sync engine
Base.metadata.create_all(magic.sync_engine)

# Use a transactional async session
async def create_user(email: str) -> None:
    async with magic.async_session() as session:
        session.add(User(email=email))
```

Use the synchronous context manager the same way when you only configured `sync_url`.

## Session-Aware Models and Repositories
`SessionMixin` and `SessionRequired` let you ensure a session is available without threading it through every call.

```python
from alchemy_magic.src.database.base.mixin import SessionMixin
from alchemy_magic.src.database.decorators.session import SessionRequired

class UserRepository(SessionMixin):

    @SessionRequired(async_mode=True)
    async def get(self, *, session, user_id: int):
        return await session.get(User, user_id)
```

Bind the repository to whatever session you are currently using:

```python
async with magic.async_session(commit=False) as session:
    RepoClass = UserRepository.with_session(session)
    repo = RepoClass()
    user = await repo.get(user_id=1)
```

If you prefer to share the same binding across several repositories, create a `DBManager` with the session and register the models or repositories once.

```python
from alchemy_magic.src.database.base.manager import DBManager

async with magic.async_session(commit=False) as session:
    manager = DBManager(session)
    RepoClass = manager.register_model(UserRepository)
    repo = RepoClass()
    user = await repo.get(user_id=1)
```

`DBManager.model()` gives you a bound subclass on demand without storing it:

```python
RepoClass = manager.model(UserRepository)
```

## FastAPI Integration
The package ships first-class FastAPI dependencies so each request receives an isolated `AsyncSession` (and therefore its own `DBManager`).

```python
from fastapi import Depends, FastAPI, HTTPException

from alchemy_magic import configure_magic
from alchemy_magic.src.database.fastapi_dependency.magic_manager import get_magic_manager

app = FastAPI()

@app.on_event("startup")
async def startup() -> None:
    configure_magic(
        async_url="sqlite+aiosqlite:///./app.db",
        sync_url="sqlite+pysqlite:///./app.db",
    )

@app.get("/users/{user_id}")
async def read_user(
    user_id: int,
    manager = Depends(get_magic_manager),
):
    RepoClass = manager.register_model(UserRepository)
    repo = RepoClass()
    user = await repo.get(user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

Need only the session? Depend directly on `alchemy_magic.src.database.magic_runtime.get_session`. For access to both the `InitMagic` factory and a session in one dependency, use `get_magic_scope`.

Each dependency is a generator, so FastAPI ensures the session is closed at the end of the request. The session instance is cached for the duration of the request; opt out with `Depends(get_session, use_cache=False)` if you genuinely need multiple sessions per request.

## Configuration Options
`configure_magic()` accepts engine and session keyword arguments so you can tune pool sizes, isolation levels, or session defaults.

```python
magic = configure_magic(
    async_url="postgresql+asyncpg://user:pass@localhost/app",
    sync_url="postgresql+psycopg://user:pass@localhost/app",
    async_engine_kwargs={"pool_size": 5, "max_overflow": 10},
    async_session_kwargs={"expire_on_commit": False},
)
```

You can call `configure_magic()` only once per process; subsequent calls replace the global singleton.

## Running the Test Suite
Use Poetry (or run the equivalent commands in your environment):

```bash
poetry run pytest
```

## License
This project is distributed under the terms specified in the repository.
