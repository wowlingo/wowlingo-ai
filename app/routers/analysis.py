from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from app.common.database import get_db
from app.models.models import User, UserAnswer, AnalysisResult, Question
from app.common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class AnalysisResponse(BaseModel):
    user_id: int
    analysis_type: str
    result_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/users/{user_id}/accuracy")
async def get_user_accuracy(user_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get user accuracy analysis"""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    # Query user answers in the date range
    answers = db.query(UserAnswer).filter(
        UserAnswer.user_id == user_id,
        UserAnswer.answered_at >= start_date,
        UserAnswer.answered_at <= end_date
    ).all()

    if not answers:
        return {
            "user_id": user_id,
            "period_days": days,
            "total_questions": 0,
            "accuracy": 0.0,
            "category_accuracy": {},
            "message": "No answers found in the specified period"
        }

    # Calculate overall accuracy
    total_questions = len(answers)
    correct_answers = sum(1 for answer in answers if answer.is_correct)
    overall_accuracy = correct_answers / total_questions if total_questions > 0 else 0

    # Calculate category-wise accuracy
    category_stats = {}
    for answer in answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if question and question.category:
            category = question.category
            if category not in category_stats:
                category_stats[category] = {"total": 0, "correct": 0}
            category_stats[category]["total"] += 1
            if answer.is_correct:
                category_stats[category]["correct"] += 1

    category_accuracy = {}
    for category, stats in category_stats.items():
        accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        category_accuracy[category] = {
            "accuracy": round(accuracy, 3),
            "total_questions": stats["total"],
            "correct_answers": stats["correct"]
        }

    return {
        "user_id": user_id,
        "period_days": days,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "accuracy": round(overall_accuracy, 3),
        "category_accuracy": category_accuracy
    }


@router.get("/users/{user_id}/confusion-patterns")
async def get_confusion_patterns(user_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get user confusion patterns analysis"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    # Get wrong answers with question details
    wrong_answers = db.query(UserAnswer, Question).join(
        Question, UserAnswer.question_id == Question.id
    ).filter(
        UserAnswer.user_id == user_id,
        UserAnswer.is_correct == False,
        UserAnswer.answered_at >= start_date,
        UserAnswer.answered_at <= end_date
    ).all()

    confusion_patterns = {}
    phonetic_confusions = {}

    for answer, question in wrong_answers:
        # Track answer confusion patterns
        correct_answer = question.correct_answer
        user_answer = answer.user_answer

        pattern_key = f"{correct_answer} -> {user_answer}"
        if pattern_key not in confusion_patterns:
            confusion_patterns[pattern_key] = 0
        confusion_patterns[pattern_key] += 1

        # Track phonetic confusions if available
        if question.phonetic_features:
            features = question.phonetic_features
            if isinstance(features, dict) and "target_phonemes" in features:
                for phoneme in features["target_phonemes"]:
                    if phoneme not in phonetic_confusions:
                        phonetic_confusions[phoneme] = 0
                    phonetic_confusions[phoneme] += 1

    # Sort by frequency
    sorted_confusions = sorted(confusion_patterns.items(), key=lambda x: x[1], reverse=True)
    sorted_phonetic = sorted(phonetic_confusions.items(), key=lambda x: x[1], reverse=True)

    return {
        "user_id": user_id,
        "period_days": days,
        "confusion_patterns": dict(sorted_confusions[:10]),  # Top 10
        "phonetic_confusions": dict(sorted_phonetic[:10]),   # Top 10
        "total_wrong_answers": len(wrong_answers)
    }


@router.get("/users/{user_id}/report")
async def get_user_report(user_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get comprehensive user analysis report"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get accuracy data
    accuracy_data = await get_user_accuracy(user_id, days, db)

    # Get confusion patterns
    confusion_data = await get_confusion_patterns(user_id, days, db)

    # Generate insights
    strengths = []
    weaknesses = []
    recommendations = []

    # Analyze strengths and weaknesses
    if accuracy_data["accuracy"] >= 0.8:
        strengths.append(f"전체 정답률이 {accuracy_data['accuracy']*100:.1f}%로 우수합니다")

    for category, stats in accuracy_data["category_accuracy"].items():
        if stats["accuracy"] >= 0.8:
            strengths.append(f"{category} 관련 단어를 잘 구분합니다 ({stats['accuracy']*100:.1f}%)")
        elif stats["accuracy"] < 0.5:
            weaknesses.append(f"{category} 관련 단어 구분에 어려움이 있습니다 ({stats['accuracy']*100:.1f}%)")

    # Generate recommendations based on confusion patterns
    for pattern, count in list(confusion_data["confusion_patterns"].items())[:3]:
        recommendations.append(f"'{pattern}' 패턴의 혼동이 {count}회 발생했습니다. 추가 연습이 필요합니다")

    for phoneme, count in list(confusion_data["phonetic_confusions"].items())[:3]:
        recommendations.append(f"'{phoneme}' 발음 구분 연습을 권장합니다 ({count}회 오답)")

    return {
        "user_id": user_id,
        "username": user.username,
        "analysis_period": f"{days}일",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_questions": accuracy_data["total_questions"],
            "overall_accuracy": accuracy_data["accuracy"],
            "total_wrong_answers": confusion_data["total_wrong_answers"]
        },
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "detailed_data": {
            "accuracy": accuracy_data,
            "confusions": confusion_data
        }
    }