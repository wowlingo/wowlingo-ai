from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from pydantic import BaseModel

from app.common.database import get_db
from app.models.models import BatchJob
from app.common.logging import get_logger
from app.core.analysis import run_analysis_batch

logger = get_logger(__name__)
router = APIRouter()


class BatchJobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    started_at: datetime
    completed_at: datetime = None
    processed_count: int
    error_count: int
    error_message: str = None

    class Config:
        from_attributes = True


@router.post("/trigger/{job_type}")
async def trigger_batch_job(job_type: str, db: Session = Depends(get_db)):
    """Manually trigger a batch job"""

    valid_job_types = ["daily_analysis", "weekly_report", "monthly_summary"]
    if job_type not in valid_job_types:
        raise HTTPException(status_code=400, detail=f"Invalid job type. Must be one of: {valid_job_types}")

    # Check if there's already a running job of this type
    running_job = db.query(BatchJob).filter(
        BatchJob.job_type == job_type,
        BatchJob.status == "running"
    ).first()

    if running_job:
        raise HTTPException(
            status_code=409,
            detail=f"A {job_type} job is already running (started at {running_job.started_at})"
        )

    # Create new batch job record
    batch_job = BatchJob(
        job_type=job_type,
        status="running"
    )
    db.add(batch_job)
    db.commit()
    db.refresh(batch_job)

    try:
        # Run the batch job
        result = await run_analysis_batch(job_type, db)

        # Update job status
        batch_job.status = "completed"
        batch_job.completed_at = datetime.now(timezone.utc)
        batch_job.processed_count = result.get("processed_count", 0)
        batch_job.result_data = result

        db.commit()

        logger.info(f"Batch job {job_type} completed successfully")
        return {
            "message": f"Batch job {job_type} completed successfully",
            "job_id": batch_job.id,
            "result": result
        }

    except Exception as e:
        # Update job status with error
        batch_job.status = "failed"
        batch_job.completed_at = datetime.now(timezone.utc)
        batch_job.error_message = str(e)
        batch_job.error_count = 1

        db.commit()

        logger.error(f"Batch job {job_type} failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch job failed: {str(e)}")


@router.get("/jobs", response_model=List[BatchJobResponse])
async def list_batch_jobs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List batch job history"""
    jobs = db.query(BatchJob).order_by(BatchJob.started_at.desc()).offset(skip).limit(limit).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=BatchJobResponse)
async def get_batch_job(job_id: int, db: Session = Depends(get_db)):
    """Get specific batch job details"""
    job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return job


@router.get("/status")
async def get_batch_status(db: Session = Depends(get_db)):
    """Get current batch processing status"""

    # Count jobs by status
    running_jobs = db.query(BatchJob).filter(BatchJob.status == "running").count()
    completed_jobs = db.query(BatchJob).filter(BatchJob.status == "completed").count()
    failed_jobs = db.query(BatchJob).filter(BatchJob.status == "failed").count()

    # Get recent jobs
    recent_jobs = db.query(BatchJob).order_by(BatchJob.started_at.desc()).limit(10).all()

    return {
        "summary": {
            "running_jobs": running_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs
        },
        "recent_jobs": [
            {
                "id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "started_at": job.started_at,
                "completed_at": job.completed_at
            }
            for job in recent_jobs
        ]
    }