"""일일 학습 피드백 생성 서비스"""
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, date, timezone

from app.common.config import settings
from app.common.logging import get_logger
from app.services.ollama import ollama_client

logger = get_logger(__name__)


def generate_daily_feedback(user_id: int, target_date: date, db: Session) -> Optional[Dict[str, Any]]:
    """
    특정 날짜의 학습 데이터를 기반으로 일일 피드백 생성

    Args:
        user_id: 사용자 ID
        target_date: 분석할 날짜
        db: 데이터베이스 세션

    Returns:
        {
            "summary": "학습 요약",
            "praise": "칭찬 메시지",
            "motivation": "동기부여 메시지"
        }
    """
    from app.models.wowlingo_models import (
        UserQuest, UserQuestItem, Quest, QuestHashtag, Hashtag
    )

    # 해당 날짜의 user_quests 조회
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())

    user_quests = db.query(UserQuest).filter(
        UserQuest.user_id == user_id,
        UserQuest.started_at >= start_datetime,
        UserQuest.started_at <= end_datetime
    ).all()

    if not user_quests:
        logger.warning(f"No quest data found for user {user_id} on {target_date}")
        return None

    # 1. 전체 정답률 계산
    total_questions = sum(uq.total_quest_item_count for uq in user_quests)
    total_correct = sum(uq.correct_quest_item_count for uq in user_quests)
    accuracy = round((total_correct / total_questions * 100) if total_questions > 0 else 0, 1)

    # 2. 완료한 퀘스트 수 (오늘) - ended_at이 NULL이 아닌 것이 완료된 퀘스트
    completed_quests = sum(1 for uq in user_quests if uq.ended_at is not None)

    # 3. 푼 퀘스트 종류 수 (오늘, distinct quest_id)
    quest_ids = {uq.quest_id for uq in user_quests}
    quest_types_count = len(quest_ids)

    # 4. 누적 완료 퀘스트 수 (전체 기간)
    total_completed_quests = db.query(UserQuest).filter(
        UserQuest.user_id == user_id,
        UserQuest.ended_at != None
    ).count()

    # 5. 현재 스테이지 진행도 조회 (user_quest_progress)
    from app.models.wowlingo_models import UserQuestProgress, Quest

    # done_yn=0 중에서 Quest.order가 가장 작은 것 찾기 (현재 진행 중인 스테이지)
    # 주의: quest_id가 아니라 Quest.order 기준!
    current_progress = db.query(UserQuestProgress).join(
        Quest, UserQuestProgress.quest_id == Quest.quest_id
    ).filter(
        UserQuestProgress.user_id == user_id,
        UserQuestProgress.done_yn == False
    ).order_by(
        Quest.order.asc(),
        UserQuestProgress.quest_id.asc()
    ).first()

    # 6. 성장 단계 판단 (스테이지 = 성장 단계)
    # Quest.order에 따라 성장 단계 매핑
    if current_progress:
        current_quest = db.query(Quest).filter(
            Quest.quest_id == current_progress.quest_id
        ).first()
        stage_order = current_quest.order if current_quest else 1
    else:
        # 진행도가 없으면 기본값
        stage_order = 1

    # 스테이지 순서에 따른 성장 단계 매핑
    if stage_order == 1:
        growth_stage = "씨앗"
    elif 2 <= stage_order <= 4:
        growth_stage = "새싹"
    elif 5 <= stage_order <= 7:
        growth_stage = "성장한 식물"
    else:  # 8 이상
        growth_stage = "열매"

    # 6. 가장 잘한 카테고리 찾기 (hashtag 기준)
    best_category, best_accuracy = find_best_category(user_quests, db)

    # 7. LLM에게 피드백 생성 요청
    prompt_config = settings.prompts.daily_learning_feedback
    system_prompt = prompt_config.get('system_prompt', '')
    user_template = prompt_config.get('user_prompt_template', '')

    user_prompt = user_template.format(
        accuracy=accuracy,
        best_category=best_category or "없음",
        best_accuracy=best_accuracy,
        total_questions=total_questions,
        completed_quests=completed_quests,
        quest_types_count=quest_types_count,
        total_completed_quests=total_completed_quests,
        growth_stage=growth_stage
    )

    prompt = system_prompt + "\n\n" + user_prompt

    data = {
        "model": settings.ollama.model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    logger.info(f"Generating daily feedback for user {user_id} on {target_date}")
    response = ollama_client._make_request("/api/generate", data)

    if response and "response" in response:
        try:
            feedback = json.loads(response["response"])
            logger.info(f"Successfully generated daily feedback for user {user_id}")

            # 25자 제한 확인 및 경고
            for key in ['summary', 'praise', 'motivation']:
                if key in feedback and len(feedback[key]) > 25:
                    logger.warning(f"{key} exceeds 25 characters: {len(feedback[key])} chars")

            return feedback
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse feedback response: {e}")
            return None

    return None


def find_best_category(user_quests: list, db: Session) -> tuple[Optional[str], float]:
    """
    가장 정답률이 높은 hashtag 카테고리 찾기

    Returns:
        (category_name, accuracy)
    """
    from app.models.wowlingo_models import (
        Quest, QuestHashtag, Hashtag, UserQuestItem
    )

    category_stats = {}

    for user_quest in user_quests:
        # 해당 quest의 hashtags 조회
        quest_hashtags = db.query(Hashtag).join(
            QuestHashtag, QuestHashtag.hashtag_id == Hashtag.hashtag_id
        ).filter(
            QuestHashtag.quest_id == user_quest.quest_id
        ).all()

        for hashtag in quest_hashtags:
            category_name = hashtag.name

            if category_name not in category_stats:
                category_stats[category_name] = {
                    'total': 0,
                    'correct': 0
                }

            category_stats[category_name]['total'] += user_quest.total_quest_item_count
            category_stats[category_name]['correct'] += user_quest.correct_quest_item_count

    # 정답률이 가장 높은 카테고리 찾기
    best_category = None
    best_accuracy = 0.0

    for category, stats in category_stats.items():
        if stats['total'] > 0:
            accuracy = (stats['correct'] / stats['total']) * 100
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_category = category

    return best_category, round(best_accuracy, 1)


def save_feedback_to_db(
    user_id: int,
    target_date: date,
    feedback: Dict[str, Any],
    db: Session
) -> int:
    """
    생성된 피드백을 ai_feedbacks 테이블에 저장

    Returns:
        ai_feedback_id
    """
    from app.models.wowlingo_models import AIFeedback, UserQuestAttempt

    # user_quest_attempt_id 찾기 또는 생성
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())

    attempt = db.query(UserQuestAttempt).filter(
        UserQuestAttempt.user_id == user_id,
        UserQuestAttempt.attempt_date >= start_datetime,
        UserQuestAttempt.attempt_date <= end_datetime
    ).first()

    if not attempt:
        # 새로운 attempt 생성
        attempt = UserQuestAttempt(
            user_id=user_id,
            login_date=datetime.now(timezone.utc),
            attempt_date=datetime.combine(target_date, datetime.now(timezone.utc).time())
        )
        db.add(attempt)
        db.flush()  # ID 생성

    # AI 피드백을 하나의 문자열로 합치기 (\n으로 구분)
    feedback_title = feedback.get('summary', '')
    feedback_message = "\n".join([
        feedback.get('praise', ''),
        feedback.get('motivation', '')
    ])

    # AI 피드백 저장 (message에만 저장, detail과 tags는 비움)
    ai_feedback = AIFeedback(
        user_quest_attempt_id=attempt.user_quest_attempt_id,
        created_at=datetime.now(timezone.utc),
        title=feedback_title,
        message=feedback_message,
        tags=None
    )

    db.add(ai_feedback)
    db.commit()
    db.refresh(ai_feedback)

    logger.info(f"Saved feedback to DB: ai_feedback_id={ai_feedback.ai_feedback_id}")

    return ai_feedback.ai_feedback_id
