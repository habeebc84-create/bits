"""Background job runner: in-process asyncio by default (Redis/ARQ when REDIS_URL set).

Stages are real, sequential, and persisted — the UI only shows what the backend reports.
"""
from __future__ import annotations

import asyncio
import logging
import threading

log = logging.getLogger("signalhunter.jobs")

_tasks: dict[str, asyncio.Task] = {}
_loop: asyncio.AbstractEventLoop | None = None


def _loop_get() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        threading.Thread(target=_loop.run_forever, daemon=True, name="shx-jobs").start()
    return _loop


def submit(investigation_id: str, coro_factory) -> str:
    loop = _loop_get()
    fut = asyncio.run_coroutine_threadsafe(_guard(investigation_id, coro_factory()), loop)
    _tasks[investigation_id] = fut  # type: ignore
    return investigation_id


async def _guard(investigation_id: str, coro):
    try:
        return await coro
    except asyncio.CancelledError:
        from ..db import SessionLocal
        from ..models import Investigation
        from .pipeline import _emit

        db = SessionLocal()
        try:
            inv = db.get(Investigation, investigation_id)
            if inv and inv.status == "running":
                inv.status = "cancelled"
                inv.stage = "cancelled"
                db.commit()
                _emit(db, inv, "cancelled", "Investigation cancelled by user.", kind="warn")
        finally:
            db.close()
        raise
    except Exception as e:  # pragma: no cover
        log.exception("job %s failed", investigation_id)
        from ..db import SessionLocal
        from ..models import Investigation
        from .pipeline import _emit

        db = SessionLocal()
        try:
            inv = db.get(Investigation, investigation_id)
            if inv:
                inv.status = "failed"
                inv.error = str(e)[:500]
                inv.retriable = 1
                db.commit()
                _emit(db, inv, inv.stage, f"Failed: {e}"[:300], kind="error")
        finally:
            db.close()


def cancel(investigation_id: str) -> bool:
    fut = _tasks.get(investigation_id)
    if fut and not fut.done():
        fut.cancel()
        return True
    return False
