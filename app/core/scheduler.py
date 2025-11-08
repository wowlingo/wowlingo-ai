from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
import asyncio
from sqlalchemy.orm import sessionmaker

from app.common.config import settings
from app.common.database import engine
from app.core.analysis import run_analysis_batch
from app.common.logging import get_logger

logger = get_logger(__name__)

# Global scheduler instance
scheduler = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def scheduled_daily_analysis():
    """Scheduled daily analysis job"""
    logger.info("Starting scheduled daily analysis")

    db = SessionLocal()
    try:
        result = await run_analysis_batch("daily_analysis", db)
        logger.info(f"Scheduled daily analysis completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled daily analysis failed: {e}")
    finally:
        db.close()


async def scheduled_weekly_report():
    """Scheduled weekly report job"""
    logger.info("Starting scheduled weekly report")

    db = SessionLocal()
    try:
        result = await run_analysis_batch("weekly_report", db)
        logger.info(f"Scheduled weekly report completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled weekly report failed: {e}")
    finally:
        db.close()


async def scheduled_monthly_summary():
    """Scheduled monthly summary job"""
    logger.info("Starting scheduled monthly summary")

    db = SessionLocal()
    try:
        result = await run_analysis_batch("monthly_summary", db)
        logger.info(f"Scheduled monthly summary completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled monthly summary failed: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the batch job scheduler"""
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler is already running")
        return

    scheduler = AsyncIOScheduler(timezone=settings.batch.timezone)

    # Add daily analysis job
    daily_hour = settings.batch.schedule.get("hour", 0)
    daily_minute = settings.batch.schedule.get("minute", 0)

    scheduler.add_job(
        scheduled_daily_analysis,
        CronTrigger(hour=daily_hour, minute=daily_minute),
        id="daily_analysis",
        name="Daily Analysis Job",
        replace_existing=True
    )

    # Add weekly report job (every Sunday at 1 AM)
    scheduler.add_job(
        scheduled_weekly_report,
        CronTrigger(day_of_week=6, hour=1, minute=0),  # Sunday = 6
        id="weekly_report",
        name="Weekly Report Job",
        replace_existing=True
    )

    # Add monthly summary job (1st day of month at 2 AM)
    scheduler.add_job(
        scheduled_monthly_summary,
        CronTrigger(day=1, hour=2, minute=0),
        id="monthly_summary",
        name="Monthly Summary Job",
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"Batch scheduler started with timezone: {settings.batch.timezone}")
    logger.info(f"Daily analysis scheduled for: {daily_hour:02d}:{daily_minute:02d}")
    logger.info("Weekly report scheduled for: Sunday 01:00")
    logger.info("Monthly summary scheduled for: 1st day of month 02:00")


def stop_scheduler():
    """Stop the batch job scheduler"""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Batch scheduler stopped")


def get_scheduler_status():
    """Get scheduler status and job information"""
    global scheduler

    if scheduler is None:
        return {"status": "stopped", "jobs": []}

    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger)
        })

    return {
        "status": "running",
        "timezone": settings.batch.timezone,
        "jobs": jobs
    }


def add_one_time_job(job_type: str, delay_seconds: int = 0):
    """Add a one-time job to run after specified delay"""
    global scheduler

    if scheduler is None:
        raise RuntimeError("Scheduler is not running")

    if job_type == "daily_analysis":
        job_func = scheduled_daily_analysis
    elif job_type == "weekly_report":
        job_func = scheduled_weekly_report
    elif job_type == "monthly_summary":
        job_func = scheduled_monthly_summary
    else:
        raise ValueError(f"Unknown job type: {job_type}")

    run_date = datetime.now(timezone.utc).replace(microsecond=0)
    if delay_seconds > 0:
        run_date = run_date.replace(second=run_date.second + delay_seconds)

    job_id = f"{job_type}_onetime_{int(datetime.now(timezone.utc).timestamp())}"

    scheduler.add_job(
        job_func,
        'date',
        run_date=run_date,
        id=job_id,
        name=f"One-time {job_type}",
        replace_existing=True
    )

    logger.info(f"Added one-time job {job_type} to run at {run_date}")
    return job_id