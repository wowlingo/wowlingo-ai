from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.models.models import User, UserAnswer, AnalysisResult, Question
from app.services.ollama import ollama_client
from app.common.logging import get_logger

logger = get_logger(__name__)


async def run_analysis_batch(job_type: str, db: Session) -> Dict[str, Any]:
    """Run batch analysis job"""

    if job_type == "daily_analysis":
        return await run_daily_analysis(db)
    elif job_type == "weekly_report":
        return await run_weekly_report(db)
    elif job_type == "monthly_summary":
        return await run_monthly_summary(db)
    else:
        raise ValueError(f"Unknown job type: {job_type}")


async def run_daily_analysis(db: Session) -> Dict[str, Any]:
    """Run daily user analysis"""

    logger.info("Starting daily analysis batch job")

    # Get users who answered questions in the last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    active_users = db.query(User.id).join(UserAnswer).filter(
        UserAnswer.answered_at >= yesterday
    ).distinct().all()

    processed_count = 0
    results = []

    for user_tuple in active_users:
        user_id = user_tuple[0]

        try:
            # Analyze user data from the last 7 days
            analysis_result = await analyze_user_performance(user_id, days=7, db=db)

            if analysis_result:
                # Save analysis result
                db_result = AnalysisResult(
                    user_id=user_id,
                    analysis_type="daily_analysis",
                    result_data=analysis_result,
                    analysis_period_start=datetime.now() - timedelta(days=7),
                    analysis_period_end=datetime.now()
                )
                db.add(db_result)
                processed_count += 1

                results.append({
                    "user_id": user_id,
                    "status": "success",
                    "insights_count": len(analysis_result.get("recommendations", []))
                })

        except Exception as e:
            logger.error(f"Failed to analyze user {user_id}: {e}")
            results.append({
                "user_id": user_id,
                "status": "error",
                "error": str(e)
            })

    db.commit()

    logger.info(f"Daily analysis completed. Processed {processed_count} users")

    return {
        "job_type": "daily_analysis",
        "processed_count": processed_count,
        "total_users": len(active_users),
        "results": results
    }


async def run_weekly_report(db: Session) -> Dict[str, Any]:
    """Run weekly comprehensive report generation"""

    logger.info("Starting weekly report batch job")

    # Get all active users
    active_users = db.query(User).filter(User.is_active == True).all()

    processed_count = 0
    reports = []

    for user in active_users:
        try:
            # Generate comprehensive report for the last 30 days
            report_data = await generate_comprehensive_report(user.id, days=30, db=db)

            if report_data:
                # Save report as analysis result
                db_result = AnalysisResult(
                    user_id=user.id,
                    analysis_type="weekly_report",
                    result_data=report_data,
                    analysis_period_start=datetime.now() - timedelta(days=30),
                    analysis_period_end=datetime.now()
                )
                db.add(db_result)
                processed_count += 1

                reports.append({
                    "user_id": user.id,
                    "username": user.username,
                    "status": "success",
                    "accuracy": report_data.get("summary", {}).get("overall_accuracy", 0)
                })

        except Exception as e:
            logger.error(f"Failed to generate report for user {user.id}: {e}")
            reports.append({
                "user_id": user.id,
                "username": user.username,
                "status": "error",
                "error": str(e)
            })

    db.commit()

    logger.info(f"Weekly report completed. Generated {processed_count} reports")

    return {
        "job_type": "weekly_report",
        "processed_count": processed_count,
        "total_users": len(active_users),
        "reports": reports
    }


async def run_monthly_summary(db: Session) -> Dict[str, Any]:
    """Run monthly system-wide summary"""

    logger.info("Starting monthly summary batch job")

    # Calculate system-wide statistics for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Total questions answered
    total_answers = db.query(UserAnswer).filter(
        UserAnswer.answered_at >= start_date
    ).count()

    # Overall accuracy
    correct_answers = db.query(UserAnswer).filter(
        UserAnswer.answered_at >= start_date,
        UserAnswer.is_correct == True
    ).count()

    overall_accuracy = correct_answers / total_answers if total_answers > 0 else 0

    # Active users count
    active_users_count = db.query(User.id).join(UserAnswer).filter(
        UserAnswer.answered_at >= start_date
    ).distinct().count()

    # Category performance
    category_stats = {}
    category_answers = db.query(
        Question.category,
        func.count(UserAnswer.id).label("total"),
        func.sum(func.cast(UserAnswer.is_correct, db.Integer)).label("correct")
    ).join(UserAnswer).filter(
        UserAnswer.answered_at >= start_date,
        Question.category.isnot(None)
    ).group_by(Question.category).all()

    for category, total, correct in category_answers:
        accuracy = correct / total if total > 0 else 0
        category_stats[category] = {
            "total_questions": total,
            "accuracy": round(accuracy, 3)
        }

    summary_data = {
        "period": "30 days",
        "total_questions": total_answers,
        "correct_answers": correct_answers,
        "overall_accuracy": round(overall_accuracy, 3),
        "active_users": active_users_count,
        "category_performance": category_stats,
        "generated_at": datetime.now().isoformat()
    }

    # Save summary
    db_result = AnalysisResult(
        user_id=None,  # System-wide summary
        analysis_type="monthly_summary",
        result_data=summary_data,
        analysis_period_start=start_date,
        analysis_period_end=end_date
    )
    db.add(db_result)
    db.commit()

    logger.info("Monthly summary completed")

    return {
        "job_type": "monthly_summary",
        "processed_count": 1,
        "summary": summary_data
    }


async def analyze_user_performance(user_id: int, days: int, db: Session) -> Dict[str, Any]:
    """Analyze individual user performance using Ollama"""

    # Get user data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    answers = db.query(UserAnswer).filter(
        UserAnswer.user_id == user_id,
        UserAnswer.answered_at >= start_date
    ).all()

    if not answers:
        return {"message": "No data available for analysis"}

    # Calculate basic statistics
    total_questions = len(answers)
    correct_answers = sum(1 for answer in answers if answer.is_correct)
    accuracy = correct_answers / total_questions

    # Get confusion patterns
    confusion_patterns = {}
    phonetic_confusions = {}

    for answer in answers:
        if not answer.is_correct:
            question = db.query(Question).filter(Question.id == answer.question_id).first()
            if question:
                pattern_key = f"{question.correct_answer} -> {answer.user_answer}"
                confusion_patterns[pattern_key] = confusion_patterns.get(pattern_key, 0) + 1

                if question.phonetic_features and isinstance(question.phonetic_features, dict):
                    features = question.phonetic_features.get("target_phonemes", [])
                    for phoneme in features:
                        phonetic_confusions[phoneme] = phonetic_confusions.get(phoneme, 0) + 1

    # Prepare data for Ollama analysis
    user_data = {
        "total_questions": total_questions,
        "accuracy": accuracy,
        "confusion_patterns": confusion_patterns,
        "phonetic_confusions": phonetic_confusions
    }

    # Get AI analysis
    ai_analysis = ollama_client.analyze_confusion_patterns(user_data)

    if ai_analysis:
        return {
            "basic_stats": user_data,
            "ai_insights": ai_analysis,
            "analysis_date": datetime.now().isoformat()
        }
    else:
        # Fallback to basic analysis if Ollama is not available
        return {
            "basic_stats": user_data,
            "message": "AI analysis not available",
            "analysis_date": datetime.now().isoformat()
        }


async def generate_comprehensive_report(user_id: int, days: int, db: Session) -> Dict[str, Any]:
    """Generate comprehensive user report"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    # Get performance analysis
    performance_data = await analyze_user_performance(user_id, days, db)

    # Calculate learning progress over time
    progress_data = calculate_learning_progress(user_id, days, db)

    # Get AI recommendations
    user_profile = {
        "user_id": user_id,
        "username": user.username,
        "performance": performance_data,
        "progress": progress_data
    }

    ai_recommendations = ollama_client.generate_personalized_recommendations(user_profile)

    return {
        "user_id": user_id,
        "username": user.username,
        "report_period": f"{days} days",
        "performance": performance_data,
        "progress": progress_data,
        "ai_recommendations": ai_recommendations or {},
        "generated_at": datetime.now().isoformat()
    }


def calculate_learning_progress(user_id: int, days: int, db: Session) -> Dict[str, Any]:
    """Calculate learning progress over time periods"""

    periods = [7, 14, 21, days]  # Weekly intervals
    progress_data = {}

    for period in periods:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period)

        answers = db.query(UserAnswer).filter(
            UserAnswer.user_id == user_id,
            UserAnswer.answered_at >= start_date
        ).all()

        if answers:
            total = len(answers)
            correct = sum(1 for answer in answers if answer.is_correct)
            accuracy = correct / total

            progress_data[f"last_{period}_days"] = {
                "total_questions": total,
                "accuracy": round(accuracy, 3),
                "period_end": end_date.isoformat()
            }

    return progress_data