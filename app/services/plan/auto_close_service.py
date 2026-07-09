from __future__ import annotations

import asyncio
from contextlib import suppress
import logging

from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database.session import SessionLocal
from app.services.plan.plan_service import auto_close_due_plans_once

logger = logging.getLogger(__name__)


def start_plan_auto_close_worker() -> asyncio.Task | None:
    if not settings.auto_close_plan_enabled:
        logger.info("Plan auto close worker disabled: AUTO_CLOSE_PLAN_ENABLED=false")
        return None
    return asyncio.create_task(_run_plan_auto_close_worker(), name="plan-auto-close-worker")


async def stop_plan_auto_close_worker(task: asyncio.Task | None) -> None:
    if task is None:
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


async def _run_plan_auto_close_worker() -> None:
    interval_seconds = settings.auto_close_plan_interval_seconds
    batch_size = settings.auto_close_plan_batch_size
    logger.info(
        "Plan auto close worker started. intervalSeconds=%s batchSize=%s",
        interval_seconds,
        batch_size,
    )

    while True:
        try:
            processed_count = await asyncio.to_thread(_auto_close_due_plans, batch_size)
            if processed_count:
                logger.info("Plan auto close worker processed plans. count=%s", processed_count)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Plan auto close worker failed")
        await asyncio.sleep(interval_seconds)


def _auto_close_due_plans(batch_size: int) -> int:
    db = SessionLocal()
    try:
        return auto_close_due_plans_once(db=db, batch_size=batch_size)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
