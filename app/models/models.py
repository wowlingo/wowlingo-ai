from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.common.database import Base


class User(Base):
    """사용자 정보 - 유연한 확장을 위해 JSON 필드 포함"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # 유연한 사용자 메타데이터 (나이, 학습 레벨, 선호도 등)
    metadata = Column(JSON, nullable=True)

    # Relationships
    answers = relationship("UserAnswer", back_populates="user")
    analysis_results = relationship("AnalysisResult", back_populates="user")


class Question(Base):
    """문제 정보 - 카테고리와 음성학적 특성을 JSON으로 유연하게 관리"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    correct_answer = Column(String(500), nullable=False)
    question_type = Column(String(50), nullable=False)  # 'multiple_choice', 'ox'

    # 선택지들 (객관식용)
    choices = Column(JSON, nullable=True)  # ["사과", "바나나", "딸기", "포도"]

    # 카테고리 및 음성학적 특성 (유연한 확장)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    phonetic_features = Column(JSON, nullable=True)  # {"target_phonemes": ["ㅂ", "ㅍ"], "difficulty": "medium"}

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # 추가 메타데이터 (오디오 파일 경로, 난이도 등)
    metadata = Column(JSON, nullable=True)

    # Relationships
    answers = relationship("UserAnswer", back_populates="question")

    # Indexes for performance
    __table_args__ = (
        Index('idx_question_category', 'category'),
        Index('idx_question_type', 'question_type'),
        Index('idx_question_active', 'is_active'),
    )


class UserAnswer(Base):
    """사용자 답변 기록"""
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(String(500), nullable=False)
    is_correct = Column(Boolean, nullable=False)

    # 응답 시간, 시도 횟수 등 추가 정보
    response_time = Column(Integer, nullable=True)  # milliseconds
    attempt_count = Column(Integer, default=1)

    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    # 세션 정보 (같은 학습 세션 그룹핑용)
    session_id = Column(String(100), nullable=True)

    # 추가 메타데이터
    metadata = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="answers")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_answers_user_id', 'user_id'),
        Index('idx_user_answers_question_id', 'question_id'),
        Index('idx_user_answers_session', 'session_id'),
        Index('idx_user_answers_date', 'answered_at'),
    )


class AnalysisResult(Base):
    """분석 결과 저장"""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_type = Column(String(100), nullable=False)  # 'accuracy', 'confusion_pattern', 'phonetic_analysis'

    # 분석 결과 데이터 (JSON으로 유연하게 저장)
    result_data = Column(JSON, nullable=False)

    # 분석 대상 기간
    analysis_period_start = Column(DateTime(timezone=True), nullable=True)
    analysis_period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 분석 버전 (알고리즘 변경 추적용)
    analysis_version = Column(String(50), default="1.0")

    # Relationships
    user = relationship("User", back_populates="analysis_results")

    # Indexes
    __table_args__ = (
        Index('idx_analysis_user_id', 'user_id'),
        Index('idx_analysis_type', 'analysis_type'),
        Index('idx_analysis_created', 'created_at'),
    )


class BatchJob(Base):
    """배치 작업 실행 이력"""
    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(100), nullable=False)  # 'daily_analysis', 'weekly_report'
    status = Column(String(50), nullable=False)  # 'running', 'completed', 'failed'

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # 처리된 레코드 수, 에러 메시지 등
    processed_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # 배치 결과 및 로그
    result_data = Column(JSON, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_batch_job_type', 'job_type'),
        Index('idx_batch_status', 'status'),
        Index('idx_batch_started', 'started_at'),
    )