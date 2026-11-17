"""`ConcurrencyLimit`: no more requests to the API in flight than database connections."""

import asyncio

from app.db import DB_CONNECTIONS, ConcurrencyLimit, engine
from app.main import app


class _Probe:
    """ASGI app that records how many calls run at the same time."""

    def __init__(self):
        self.running = 0
        self.max_running = 0

    async def __call__(self, scope, receive, send):
        self.running += 1
        self.max_running = max(self.max_running, self.running)
        await asyncio.sleep(0.01)
        self.running -= 1


async def _call_many(middleware: ConcurrencyLimit, path: str, count: int) -> None:
    scope = {"type": "http", "path": path}
    await asyncio.gather(*(middleware(scope, None, None) for _ in range(count)))


async def test_api_requests_wait_for_a_free_slot():
    probe = _Probe()
    await _call_many(ConcurrencyLimit(probe, limit=3), "/api/v1/suppliers", 20)
    assert probe.max_running == 3


async def test_other_paths_are_not_limited():
    probe = _Probe()
    await _call_many(ConcurrencyLimit(probe, limit=3), "/health", 20)
    assert probe.max_running == 20


def test_the_limit_is_the_size_of_the_pool():
    """Never more requests than connections, and never more connections than the 40
    threads that run the synchronous routes."""
    assert engine.pool.size() + engine.pool._max_overflow == DB_CONNECTIONS <= 40
    limits = [m for m in app.user_middleware if m.cls is ConcurrencyLimit]
    assert len(limits) == 1
    assert limits[0].kwargs == {"path_prefix": "/api/"}
