"""APScheduler를 사용한 크론 스케줄러 서비스."""
from __future__ import annotations

import logging
from datetime import timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.crawler import run_crawl_with_log, promote_stable_items

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    """스케줄러를 시작한다. 매일 18:00 UTC (KST 03:00)에 크롤링 실행."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("스케줄러가 이미 실행 중입니다.")
        return

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        run_crawl_with_log,
        trigger=CronTrigger(hour=18, minute=0, timezone="UTC"),
        id="daily_crawl",
        name="매일 18:00 UTC 크롤링",
        replace_existing=True,
        misfire_grace_time=3600,  # 1시간 내 재실행 허용
    )
    _scheduler.add_job(
        promote_stable_items,
        trigger=CronTrigger(day_of_week="sun", hour=0, minute=0, timezone="UTC"),
        id="weekly_stable_promote",
        name="매주 일요일 00:00 UTC stable 전환",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    _scheduler.start()
    logger.info("스케줄러 시작: 매일 18:00 UTC에 크롤링 실행")


def stop_scheduler() -> None:
    """스케줄러를 종료한다."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("스케줄러 종료")
    _scheduler = None


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler
