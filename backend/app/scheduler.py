from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings


def start_scheduler() -> AsyncIOScheduler:
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")

    scheduler.add_job(
        _scheduled_pipeline,
        CronTrigger(hour=settings.fetch_cron_hour),
        id="daily_pipeline",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    return scheduler


async def _scheduled_pipeline() -> None:
    from app.pipeline.orchestrator import run_pipeline

    try:
        stats = await run_pipeline()
        print(f"[scheduler] pipeline selesai: {stats}")
    except Exception as exc:  # noqa: BLE001
        print(f"[scheduler] pipeline gagal: {exc}")
