from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from pydantic import BaseModel

from app.common.database import get_db
from app.models.wowlingo_models import AIFeedback
from app.common.logging import get_logger
from app.core.feedback_generator import generate_daily_feedbacks

logger = get_logger(__name__)
router = APIRouter()


class BatchJobResponse(BaseModel):
    job_type: str
    status: str
    processed_count: int
    error_count: int = 0
    message: str = None

    class Config:
        from_attributes = True


@router.post("/trigger/{job_type}")
async def trigger_batch_job(job_type: str, db: Session = Depends(get_db)):
    """Manually trigger a batch job"""

    valid_job_types = ["daily_feedback"]
    if job_type not in valid_job_types:
        raise HTTPException(status_code=400, detail=f"Invalid job type. Must be one of: {valid_job_types}")

    try:
        if job_type == "daily_feedback":
            result = await generate_daily_feedbacks(db)

        logger.info(f"Batch job {job_type} completed successfully")
        return {
            "message": f"Batch job {job_type} completed successfully",
            "result": result
        }

    except Exception as e:
        logger.error(f"Batch job {job_type} failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch job failed: {str(e)}")


@router.get("/feedbacks/recent")
async def list_recent_feedbacks(limit: int = 50, db: Session = Depends(get_db)):
    """List recent AI feedbacks"""
    feedbacks = db.query(AIFeedback).order_by(
        AIFeedback.created_at.desc()
    ).limit(limit).all()
    
    return [{
        "feedback_id": f.ai_feedback_id,
        "user_quest_attempt_id": f.user_quest_attempt_id,
        "created_at": f.created_at,
        "title": f.title,
        "message": f.message,
        "tags": f.tags
    } for f in feedbacks]


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    from app.core.scheduler import get_scheduler_status
    return get_scheduler_status()