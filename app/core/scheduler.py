from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
import asyncio
from sqlalchemy.orm import sessionmaker

from app.common.config import settings
from app.common.database import engine
from app.core.feedback_generator import generate_daily_feedbacks
from app.common.logging import get_logger

logger = get_logger(__name__)

# Global scheduler instance
scheduler = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def scheduled_daily_feedback():
    """Scheduled daily AI feedback generation for users"""
    logger.info("Starting scheduled daily AI feedback generation")

    db = SessionLocal()
    try:
        result = await generate_daily_feedbacks(db)
        logger.info(f"Daily feedback generation completed: {result}")
    except Exception as e:
        logger.error(f"Daily feedback generation failed: {e}")
    finally:
        db.close()


async def scheduled_daily_analysis():
    """Scheduled daily analysis job (placeholder)"""
    logger.info("Daily analysis job - currently disabled")
    return {"status": "skipped", "reason": "Not implemented"}


async def scheduled_weekly_report():
    """Scheduled weekly report job (placeholder)"""
    logger.info("Weekly report job - currently disabled")
    return {"status": "skipped", "reason": "Not implemented"}


async def scheduled_monthly_summary():
    """Scheduled monthly summary job (placeholder)"""
    logger.info("Monthly summary job - currently disabled")
    return {"status": "skipped", "reason": "Not implemented"}


def start_scheduler():
    """Start the batch job scheduler with config-driven settings"""
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler is already running")
        return

    scheduler = AsyncIOScheduler(timezone=settings.batch.timezone)
    logger.info(f"Initializing scheduler with timezone: {settings.batch.timezone}")

    # Add daily feedback job (최우선)
    if settings.batch.daily_feedback.enabled:
        scheduler.add_job(
            scheduled_daily_feedback,
            CronTrigger(
                hour=settings.batch.daily_feedback.hour,
                minute=settings.batch.daily_feedback.minute,
                timezone=settings.batch.timezone
            ),
            id="daily_feedback",
            name="Daily AI Feedback Generation",
            replace_existing=True
        )
        logger.info(f"Daily feedback scheduled for: {settings.batch.daily_feedback.hour:02d}:{settings.batch.daily_feedback.minute:02d} {settings.batch.timezone}")

    # Add daily analysis job
    if settings.batch.daily_analysis.enabled:
        scheduler.add_job(
            scheduled_daily_analysis,
            CronTrigger(
                hour=settings.batch.daily_analysis.hour,
                minute=settings.batch.daily_analysis.minute,
                timezone=settings.batch.timezone
            ),
            id="daily_analysis",
            name="Daily Analysis Job",
            replace_existing=True
        )
        logger.info(f"Daily analysis scheduled for: {settings.batch.daily_analysis.hour:02d}:{settings.batch.daily_analysis.minute:02d}")

    # Add weekly report job
    if settings.batch.weekly_report.enabled:
        scheduler.add_job(
            scheduled_weekly_report,
            CronTrigger(
                day_of_week=settings.batch.weekly_report.day_of_week,
                hour=settings.batch.weekly_report.hour,
                minute=settings.batch.weekly_report.minute,
                timezone=settings.batch.timezone
            ),
            id="weekly_report",
            name="Weekly Report Job",
            replace_existing=True
        )
        logger.info(f"Weekly report scheduled for: day_of_week={settings.batch.weekly_report.day_of_week} {settings.batch.weekly_report.hour:02d}:{settings.batch.weekly_report.minute:02d}")

    # Add monthly summary job
    if settings.batch.monthly_summary.enabled:
        scheduler.add_job(
            scheduled_monthly_summary,
            CronTrigger(
                day=settings.batch.monthly_summary.day,
                hour=settings.batch.monthly_summary.hour,
                minute=settings.batch.monthly_summary.minute,
                timezone=settings.batch.timezone
            ),
            id="monthly_summary",
            name="Monthly Summary Job",
            replace_existing=True
        )
        logger.info(f"Monthly summary scheduled for: day={settings.batch.monthly_summary.day} {settings.batch.monthly_summary.hour:02d}:{settings.batch.monthly_summary.minute:02d}")

    scheduler.start()
    logger.info("Batch scheduler started successfully")


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

    if job_type == "daily_feedback":
        job_func = scheduled_daily_feedback
    elif job_type == "daily_analysis":
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