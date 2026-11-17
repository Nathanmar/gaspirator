"""Database engine, session and declarative base (SQLAlchemy 2, PostgreSQL)."""

import asyncio
from collections.abc import Iterator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from starlette.types import ASGIApp, Receive, Scope, Send

from app.settings import get_settings

# Deterministic constraint names, so Alembic migrations stay stable.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# Database connections of one process. A request uses at most one (one session per
# request), so `ConcurrencyLimit` lets at most that many requests run at the same time.
# With several workers, keep workers × DB_CONNECTIONS under the PostgreSQL max_connections
# (100 by default).
POOL_SIZE = 10
POOL_MAX_OVERFLOW = 10
DB_CONNECTIONS = POOL_SIZE + POOL_MAX_OVERFLOW

engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    pool_size=POOL_SIZE,
    max_overflow=POOL_MAX_OVERFLOW,
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class ConcurrencyLimit:
    """ASGI middleware: at most `limit` requests under `path_prefix` run at the same time,
    the others wait their turn.

    The routes and `get_session` are synchronous: FastAPI runs each of their steps in a
    pool of 40 threads, and a request keeps its connection from one step to the next. With
    more requests in flight than connections, every thread can end up waiting for a
    connection held by requests that wait for a thread: the API freezes until the pool
    timeout (30 s), then answers 500 (see Charge.md). Waiting here takes no thread, and a
    thread never waits for a connection as long as `limit` <= DB_CONNECTIONS <= 40.
    """

    def __init__(self, app: ASGIApp, limit: int = DB_CONNECTIONS, path_prefix: str = "/api/"):
        self.app = app
        self.path_prefix = path_prefix
        self._slots = asyncio.Semaphore(limit)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith(self.path_prefix):
            await self.app(scope, receive, send)
            return
        async with self._slots:
            await self.app(scope, receive, send)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with SessionLocal() as session:
        yield session
