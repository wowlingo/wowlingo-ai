"""일일 학습 피드백 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from datetime import date, datetime, timezone
from typing import Optional, List

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


class AIFeedbackItem(BaseModel):
    """AI 피드백 아이템"""
    ai_feedback_id: int
    user_quest_attempt_id: int
    created_at: Optional[datetime]
    title: Optional[str]
    message: Optional[str]
    tags: Optional[str]

    class Config:
        from_attributes = True


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


@router.get("/db-test")
def test_database_connection():
    """
    데이터베이스 연결 테스트 (PyMySQL 헬퍼 사용)

    Returns:
        데이터베이스 연결 상태
    """
    from app.common.db_helper import execute_query

    try:
        # 연결 테스트
        test_result = execute_query("SELECT 1 as test", fetch_one=True)

        # 데이터베이스 버전 확인
        version_result = execute_query("SELECT VERSION() as version", fetch_one=True)

        logger.info("Database connection test successful")
        return {
            "status": "connected",
            "message": "Database connection successful",
            "database_version": version_result['version'],
            "test_query_result": test_result['test']
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Database connection test failed: {e}\n{error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )


@router.get("/ai-feedbacks/latest")
def get_latest_ai_feedbacks():  # async 제거 - 동기 함수로 변경
    """
    ai_feedbacks 테이블에서 최근 10개 데이터 가져오기 (PyMySQL 직접 사용)

    Returns:
        최근 10개의 AI 피드백 레코드
    """
    import pymysql
    from app.common.config import settings

    try:
        # PyMySQL로 직접 연결
        conn = pymysql.connect(
            host=settings.database.host,
            port=settings.database.port,
            user=settings.database.username,
            password=settings.database.password,
            database=settings.database.database,
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor  # Dictionary cursor for easier JSON conversion
        )

        cursor = conn.cursor()

        # 최근 10개 AI 피드백 조회
        query = """
            SELECT
                ai_feedback_id,
                user_quest_attempt_id,
                created_at,
                message,
                detail,
                tags
            FROM ai_feedbacks
            ORDER BY created_at DESC
            LIMIT 10
        """
        cursor.execute(query)
        feedbacks = cursor.fetchall()

        cursor.close()
        conn.close()

        logger.info(f"Retrieved {len(feedbacks)} latest AI feedbacks")
        return {
            "count": len(feedbacks),
            "feedbacks": feedbacks
        }
    except Exception as e:
        logger.error(f"Failed to retrieve AI feedbacks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve AI feedbacks: {str(e)}"
        )


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

    # message를 \n으로 분리 (summary, praise, motivation)
    feedback_parts = (latest_feedback.message or "").split("\n")
    summary = feedback_parts[0] if len(feedback_parts) > 0 else ""
    praise = feedback_parts[1] if len(feedback_parts) > 1 else ""
    motivation = feedback_parts[2] if len(feedback_parts) > 2 else ""

    return FeedbackResponse(
        summary=summary,
        praise=praise,
        motivation=motivation,
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

    # message를 \n으로 분리 (summary, praise, motivation)
    feedback_parts = (feedback.message or "").split("\n")
    summary = feedback_parts[0] if len(feedback_parts) > 0 else ""
    praise = feedback_parts[1] if len(feedback_parts) > 1 else ""
    motivation = feedback_parts[2] if len(feedback_parts) > 2 else ""

    return FeedbackResponse(
        summary=summary,
        praise=praise,
        motivation=motivation,
        ai_feedback_id=feedback.ai_feedback_id
    )
