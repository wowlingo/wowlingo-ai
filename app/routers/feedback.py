"""일일 학습 피드백 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

from app.common.database import get_db
from app.common.logging import get_logger
from app.services.feedback import generate_daily_feedback, save_feedback_to_db

logger = get_logger(__name__)
router = APIRouter()


class FeedbackResponse(BaseModel):
    """피드백 응답"""
    summary: str
    praise: str
    motivation: str
    ai_feedback_id: Optional[int] = None

    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    """피드백 생성 요청"""
    user_id: int
    target_date: Optional[str] = None  # YYYY-MM-DD 형식, 없으면 오늘


@router.post("/generate", response_model=FeedbackResponse)
async def generate_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    일일 학습 피드백 생성

    학습 12시간 후에 호출되도록 스케줄링 권장

    요청 예시:
    ```json
    {
        "user_id": 1,
        "target_date": "2025-01-15"  // 선택사항, 없으면 오늘
    }
    ```

    응답 예시:
    ```json
    {
        "summary": "오늘 퀴즈 15개 중 12개 맞혔어요!",
        "praise": "귀가 밝아지고 있어요 ☀️",
        "motivation": "새싹으로 자라날 준비 중이에요 🌿",
        "ai_feedback_id": 123
    }
    ```
    """
    # 날짜 파싱
    if request.target_date:
        try:
            target_date = datetime.strptime(request.target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        target_date = date.today()

    # 피드백 생성
    feedback = generate_daily_feedback(request.user_id, target_date, db)

    if not feedback:
        raise HTTPException(
            status_code=404,
            detail=f"No learning data found for user {request.user_id} on {target_date}"
        )

    # DB에 저장
    try:
        ai_feedback_id = save_feedback_to_db(
            request.user_id,
            target_date,
            feedback,
            db
        )
        feedback['ai_feedback_id'] = ai_feedback_id
    except Exception as e:
        logger.error(f"Failed to save feedback to DB: {e}")
        # 피드백은 반환하되, DB 저장 실패는 경고만

    return FeedbackResponse(**feedback)


@router.get("/user/{user_id}/latest", response_model=FeedbackResponse)
async def get_latest_feedback(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    사용자의 최신 피드백 조회

    Args:
        user_id: 사용자 ID

    Returns:
        가장 최근에 생성된 피드백
    """
    from app.models.wowlingo_models import AIFeedback, UserQuestAttempt

    # 최신 피드백 조회
    latest_feedback = db.query(AIFeedback).join(
        UserQuestAttempt,
        AIFeedback.user_quest_attempt_id == UserQuestAttempt.user_quest_attempt_id
    ).filter(
        UserQuestAttempt.user_id == user_id
    ).order_by(
        AIFeedback.created_at.desc()
    ).first()

    if not latest_feedback:
        raise HTTPException(
            status_code=404,
            detail=f"No feedback found for user {user_id}"
        )

    return FeedbackResponse(
        summary=latest_feedback.message or "",
        praise=latest_feedback.detail or "",
        motivation=latest_feedback.tags or "",
        ai_feedback_id=latest_feedback.ai_feedback_id
    )


@router.get("/user/{user_id}/date/{target_date}", response_model=FeedbackResponse)
async def get_feedback_by_date(
    user_id: int,
    target_date: str,
    db: Session = Depends(get_db)
):
    """
    특정 날짜의 피드백 조회

    Args:
        user_id: 사용자 ID
        target_date: 날짜 (YYYY-MM-DD)

    Returns:
        해당 날짜의 피드백
    """
    from app.models.wowlingo_models import AIFeedback, UserQuestAttempt

    # 날짜 파싱
    try:
        parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    start_datetime = datetime.combine(parsed_date, datetime.min.time())
    end_datetime = datetime.combine(parsed_date, datetime.max.time())

    # 해당 날짜의 피드백 조회
    feedback = db.query(AIFeedback).join(
        UserQuestAttempt,
        AIFeedback.user_quest_attempt_id == UserQuestAttempt.user_quest_attempt_id
    ).filter(
        UserQuestAttempt.user_id == user_id,
        AIFeedback.created_at >= start_datetime,
        AIFeedback.created_at <= end_datetime
    ).first()

    if not feedback:
        raise HTTPException(
            status_code=404,
            detail=f"No feedback found for user {user_id} on {target_date}"
        )

    return FeedbackResponse(
        summary=feedback.message or "",
        praise=feedback.detail or "",
        motivation=feedback.tags or "",
        ai_feedback_id=feedback.ai_feedback_id
    )
