"""AI 피드백 생성 모듈"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import asyncio

from app.models.wowlingo_models import User, UserQuest, UserQuestAttempt, AIFeedback, Quest
from app.services.ollama import ollama_client
from app.common.logging import get_logger

logger = get_logger(__name__)


async def generate_daily_feedbacks(db: Session, batch_size: int = 50) -> Dict[str, Any]:
    """
    모든 활성 사용자에 대한 데일리 AI 피드백 생성
    매일 밤 실행되어 당일 학습 활동에 대한 피드백을 생성
    """
    logger.info("Starting daily AI feedback generation batch")
    
    # 오늘 날짜 (KST 기준)
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=kst)
    today_end = today_start + timedelta(days=1)
    
    # UTC로 변환
    today_start_utc = today_start.astimezone(timezone.utc)
    today_end_utc = today_end.astimezone(timezone.utc)
    
    try:
        # 오늘 학습한 사용자 조회
        active_users = db.query(User.user_id).join(
            UserQuest, User.user_id == UserQuest.user_id
        ).filter(
            and_(
                UserQuest.started_at >= today_start_utc,
                UserQuest.started_at < today_end_utc
            )
        ).distinct().all()
        
        logger.info(f"Found {len(active_users)} active users for today")
        
        processed_count = 0
        error_count = 0
        results = []
        
        # 배치 단위로 처리
        for i in range(0, len(active_users), batch_size):
            batch_users = active_users[i:i+batch_size]
            
            # 병렬 처리를 위한 태스크 생성
            tasks = []
            for user_tuple in batch_users:
                user_id = user_tuple[0]
                tasks.append(generate_user_daily_feedback(user_id, today_start_utc, today_end_utc, db))
            
            # 배치 실행
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 처리
            for user_id, result in zip([u[0] for u in batch_users], batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to generate feedback for user {user_id}: {result}")
                    error_count += 1
                    results.append({
                        "user_id": user_id,
                        "status": "error",
                        "error": str(result)
                    })
                elif result:
                    processed_count += 1
                    results.append({
                        "user_id": user_id,
                        "status": "success",
                        "feedback_id": result.get("feedback_id")
                    })
            
            # 배치 간 짧은 대기
            await asyncio.sleep(0.1)
        
        db.commit()
        
        logger.info(f"Daily feedback generation completed. Processed: {processed_count}, Errors: {error_count}")
        
        return {
            "job_type": "daily_feedback",
            "date": today.isoformat(),
            "total_users": len(active_users),
            "processed_count": processed_count,
            "error_count": error_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Daily feedback generation batch failed: {e}")
        db.rollback()
        raise


async def generate_user_daily_feedback(user_id: int, start_time: datetime, end_time: datetime, db: Session) -> Dict[str, Any]:
    """
    개별 사용자의 데일리 피드백 생성
    """
    try:
        # 사용자의 오늘 학습 데이터 조회
        user_quests = db.query(UserQuest).filter(
            and_(
                UserQuest.user_id == user_id,
                UserQuest.started_at >= start_time,
                UserQuest.started_at < end_time
            )
        ).all()
        
        if not user_quests:
            logger.debug(f"No learning data found for user {user_id} on this day")
            return None
        
        # 학습 통계 계산
        total_items = sum(uq.total_quest_item_count for uq in user_quests)
        correct_items = sum(uq.correct_quest_item_count for uq in user_quests)
        total_time = sum(uq.time_spent or 0 for uq in user_quests)
        avg_accuracy = sum(float(uq.accuracy_rate) for uq in user_quests) / len(user_quests) if user_quests else 0
        
        # 문제 유형별 성능 분석
        quest_performance = []
        for uq in user_quests:
            quest = db.query(Quest).filter(Quest.quest_id == uq.quest_id).first()
            if quest:
                quest_performance.append({
                    "quest_title": quest.title,
                    "quest_type": quest.type,
                    "accuracy": float(uq.accuracy_rate),
                    "items_completed": uq.total_quest_item_count
                })
        
        # AI 피드백 생성을 위한 데이터 준비
        learning_summary = {
            "total_questions": total_items,
            "correct_answers": correct_items,
            "accuracy_rate": avg_accuracy,
            "time_spent_minutes": total_time // 60 if total_time else 0,
            "quests_completed": len(user_quests),
            "quest_details": quest_performance
        }
        
        # Ollama를 사용한 AI 피드백 생성
        ai_feedback = generate_ai_feedback_content(learning_summary)
        
        # UserQuestAttempt 레코드 생성 또는 조회
        kst = timezone(timedelta(hours=9))
        today_kst = datetime.now(kst).date()
        attempt_date = datetime.combine(today_kst, datetime.min.time()).replace(tzinfo=kst)
        
        user_attempt = db.query(UserQuestAttempt).filter(
            and_(
                UserQuestAttempt.user_id == user_id,
                func.date(UserQuestAttempt.attempt_date) == attempt_date.date()
            )
        ).first()
        
        if not user_attempt:
            user_attempt = UserQuestAttempt(
                user_id=user_id,
                login_date=datetime.now(timezone.utc),
                attempt_date=attempt_date
            )
            db.add(user_attempt)
            db.flush()
        
        # AI 피드백 저장
        feedback_record = AIFeedback(
            user_quest_attempt_id=user_attempt.user_quest_attempt_id,
            created_at=datetime.now(timezone.utc),
            title=ai_feedback["title"],
            message=ai_feedback["message"],
            tags=ai_feedback["tags"]
        )
        db.add(feedback_record)
        db.flush()
        
        # UserQuestAttempt에 피드백 ID 연결
        user_attempt.ai_feedback_id = feedback_record.ai_feedback_id
        
        logger.debug(f"Generated feedback for user {user_id}: feedback_id={feedback_record.ai_feedback_id}")
        
        return {
            "feedback_id": feedback_record.ai_feedback_id,
            "user_id": user_id,
            "summary": learning_summary
        }
        
    except Exception as e:
        logger.error(f"Failed to generate feedback for user {user_id}: {e}")
        raise


def generate_ai_feedback_content(learning_summary: Dict[str, Any]) -> Dict[str, str]:
    """
    학습 요약 데이터를 기반으로 AI 피드백 콘텐츠 생성
    """
    try:
        # Ollama를 사용한 피드백 생성
        prompt = f"""
        다음 학습 데이터를 분석하여 격려와 동기부여가 담긴 피드백을 생성해주세요:
        
        - 총 문제 수: {learning_summary['total_questions']}
        - 맞춘 문제 수: {learning_summary['correct_answers']}
        - 정답률: {learning_summary['accuracy_rate']:.1f}%
        - 학습 시간: {learning_summary['time_spent_minutes']}분
        - 완료한 퀘스트: {learning_summary['quests_completed']}개
        
        퀘스트별 성과:
        {format_quest_details(learning_summary.get('quest_details', []))}
        
        다음 형식으로 응답해주세요:
        1. 제목 (15자 이내의 오늘 학습 한 줄 요약)
        2. 메시지 (100자 이내의 격려 메시지)
        3. 해시태그 (쉼표로 구분된 3-5개 태그)
        """
        
        response = ollama_client.generate_feedback(prompt)
        
        if response:
            return parse_ai_response(response)
        else:
            # Ollama 사용 불가 시 기본 피드백
            return generate_fallback_feedback(learning_summary)
            
    except Exception as e:
        logger.warning(f"Failed to generate AI feedback, using fallback: {e}")
        return generate_fallback_feedback(learning_summary)


def format_quest_details(quest_details: List[Dict]) -> str:
    """퀘스트 상세 정보 포맷팅"""
    if not quest_details:
        return "상세 정보 없음"
    
    details = []
    for quest in quest_details[:5]:  # 최대 5개까지만
        details.append(f"- {quest['quest_title']}: 정답률 {quest['accuracy']:.1f}%")
    
    return "\n".join(details)


def parse_ai_response(response: str) -> Dict[str, str]:
    """AI 응답을 파싱하여 피드백 형식으로 변환"""
    lines = response.strip().split("\n")
    
    title = "오늘도 열심히 학습하셨네요!"
    message = "꾸준한 학습이 실력 향상의 지름길입니다. 내일도 화이팅!"
    tags = "#영어학습,#매일공부,#화이팅"
    
    for line in lines:
        if "제목" in line or "title" in line.lower():
            title = line.split(":", 1)[1].strip() if ":" in line else title
        elif "메시지" in line or "message" in line.lower():
            message = line.split(":", 1)[1].strip() if ":" in line else message
        elif "해시태그" in line or "tag" in line.lower():
            tags = line.split(":", 1)[1].strip() if ":" in line else tags
    
    # 길이 제한 적용
    title = title[:100]  # DB 컬럼 제한
    message = message[:500]  # DB 컬럼 제한
    tags = tags[:500]  # DB 컬럼 제한
    
    return {
        "title": title,
        "message": message,
        "tags": tags
    }


def generate_fallback_feedback(learning_summary: Dict[str, Any]) -> Dict[str, str]:
    """AI 사용 불가 시 기본 피드백 생성"""
    accuracy = learning_summary['accuracy_rate']
    total_questions = learning_summary['total_questions']
    
    if accuracy >= 80:
        title = "훌륭한 성과입니다!"
        message = f"정답률 {accuracy:.1f}%! 매우 우수한 학습 결과입니다. 이 페이스를 유지해주세요!"
        tags = "#우수학습자,#높은정답률,#꾸준한성장"
    elif accuracy >= 60:
        title = "좋은 진전이 있네요!"
        message = f"{total_questions}문제 중 {learning_summary['correct_answers']}문제 성공! 조금만 더 노력하면 더 좋은 결과가 있을 거예요."
        tags = "#성장중,#꾸준히학습,#노력의결실"
    else:
        title = "오늘도 한 걸음 전진!"
        message = f"학습을 완료한 것만으로도 대단해요! 틀린 문제를 복습하면 더 빠른 성장이 가능할 거예요."
        tags = "#도전정신,#복습필요,#화이팅"
    
    return {
        "title": title,
        "message": message,
        "tags": tags
    }