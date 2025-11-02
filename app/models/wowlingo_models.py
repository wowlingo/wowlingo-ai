"""Wowlingo 실제 데이터베이스 모델"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, DECIMAL, BigInteger, SmallInteger, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.common.database import Base


class User(Base):
    """사용자"""
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    auth_type = Column(String(20), nullable=False, comment="인증 타입 (google, kakao, apple 등)")
    auth = Column(String(100), nullable=False, comment="외부 인증 ID")
    nickname = Column(String(50), nullable=False, comment="닉네임")

    # Relationships
    quest_attempts = relationship("UserQuestAttempt", back_populates="user")
    user_quests = relationship("UserQuest", back_populates="user")


class Quest(Base):
    """문제집"""
    __tablename__ = "quests"

    quest_id = Column(Integer, primary_key=True, autoincrement=True)
    quest_item_count = Column(SmallInteger, nullable=False, default=0, comment="Quest Item 갯수")
    order = Column(SmallInteger, nullable=False, default=0, comment="순서")
    title = Column(String(100), nullable=False, comment="문제집 타이틀")
    type = Column(String(100), nullable=False, comment="문제집 타입")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(50))
    updated_by = Column(String(50))

    # Relationships
    quest_items = relationship("QuestItem", back_populates="quest")
    quest_hashtags = relationship("QuestHashtag", back_populates="quest")
    user_quests = relationship("UserQuest", back_populates="quest")


class QuestItem(Base):
    """문제"""
    __tablename__ = "quest_items"

    quest_item_id = Column(Integer, primary_key=True, autoincrement=True)
    quest_id = Column(Integer, ForeignKey("quests.quest_id"), nullable=False)
    type = Column(String(20), nullable=False, comment="문제 타입")
    has_answer = Column(Boolean, nullable=False, default=False, comment="답변 여부")
    question1 = Column(BigInteger)
    question2 = Column(BigInteger)
    answer1 = Column(BigInteger, comment="quest_item_unit 중 한가지의 id")
    answer2 = Column(BigInteger, comment="quest_item_unit 중 한가지의 id")
    answer_sq = Column(String(10), comment="평서문/의문문 답변")
    answer_ox = Column(String(10), comment="Same/Different 답변")

    # Relationships
    quest = relationship("Quest", back_populates="quest_items")
    user_quest_items = relationship("UserQuestItem", back_populates="quest_item")


class QuestItemUnit(Base):
    """문제 유닛"""
    __tablename__ = "quest_item_units"

    quest_item_unit_id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(20), nullable=False, comment="유닛 타입")
    str = Column(Text, comment="문자열")
    url_normal = Column(String(500), comment="일반 URL")
    url_slow = Column(String(500), comment="느린 URL")
    remark = Column(Text, comment="비고")

    # Relationships
    unit_hashtags = relationship("QuestItemUnitHashtag", back_populates="quest_item_unit")


class UserQuest(Base):
    """사용자 퀘스트 수행 기록"""
    __tablename__ = "user_quests"

    user_quest_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    quest_id = Column(BigInteger, ForeignKey("quests.quest_id"), nullable=False)
    done_yn = Column(Boolean, nullable=False, default=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime)
    time_spent = Column(Integer)
    progress_rate = Column(SmallInteger, nullable=False, default=0, comment="진행률")
    total_quest_item_count = Column(Integer, nullable=False)
    correct_quest_item_count = Column(Integer, default=0)
    accuracy_rate = Column(DECIMAL(5, 2), nullable=False, default=0.00)

    # Relationships
    user = relationship("User", back_populates="user_quests")
    quest = relationship("Quest", back_populates="user_quests")
    user_quest_items = relationship("UserQuestItem", back_populates="user_quest")


class UserQuestItem(Base):
    """사용자 문제 답변 기록"""
    __tablename__ = "user_quest_items"

    user_quest_item_id = Column(Integer, primary_key=True, autoincrement=True)
    user_quest_id = Column(Integer, ForeignKey("user_quests.user_quest_id"), nullable=False)
    quest_item_id = Column(BigInteger, ForeignKey("quest_items.quest_item_id"), nullable=False)
    user_answer = Column(Text, comment="선택한 답변")
    correct_yn = Column(Boolean)
    time_spent = Column(Integer)
    attempt_at = Column(DateTime)
    attempt_count = Column(Integer, default=1)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)

    # Relationships
    user_quest = relationship("UserQuest", back_populates="user_quest_items")
    quest_item = relationship("QuestItem", back_populates="user_quest_items")


class Hashtag(Base):
    """해시태그"""
    __tablename__ = "hashtags"

    hashtag_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(16), nullable=False, comment="해시태그 코드")
    name = Column(String(50), nullable=False, comment="해시태그 문자열")

    # Relationships
    quest_hashtags = relationship("QuestHashtag", back_populates="hashtag")
    unit_hashtags = relationship("QuestItemUnitHashtag", back_populates="hashtag")


class QuestHashtag(Base):
    """퀘스트-해시태그 매핑"""
    __tablename__ = "quest_hashtags"

    quest_hashtag_id = Column(Integer, primary_key=True, autoincrement=True)
    quest_id = Column(BigInteger, ForeignKey("quests.quest_id"), nullable=False)
    hashtag_id = Column(BigInteger, ForeignKey("hashtags.hashtag_id"), nullable=False)

    # Relationships
    quest = relationship("Quest", back_populates="quest_hashtags")
    hashtag = relationship("Hashtag", back_populates="quest_hashtags")


class QuestItemUnitHashtag(Base):
    """문제유닛-해시태그 매핑"""
    __tablename__ = "quest_item_unit_hashtags"

    quest_item_unit_hashtag_id = Column(Integer, primary_key=True, autoincrement=True)
    quest_item_unit_id = Column(Integer, ForeignKey("quest_item_units.quest_item_unit_id"), nullable=False)
    hashtag_id = Column(Integer, ForeignKey("hashtags.hashtag_id"))

    # Relationships
    quest_item_unit = relationship("QuestItemUnit", back_populates="unit_hashtags")
    hashtag = relationship("Hashtag", back_populates="unit_hashtags")


class UserQuestAttempt(Base):
    """사용자 학습 시도 기록 (달력)"""
    __tablename__ = "user_quest_attempts"

    user_quest_attempt_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    login_date = Column(TIMESTAMP, nullable=False, comment="로그인 날짜")
    attempt_date = Column(TIMESTAMP, comment="학습 시도 날짜")
    ai_feedback_id = Column(BigInteger, ForeignKey("ai_feedbacks.ai_feedback_id"), comment="AI 피드백 Id")

    # Relationships
    user = relationship("User", back_populates="quest_attempts")
    ai_feedback = relationship("AIFeedback", back_populates="quest_attempts")


class AIFeedback(Base):
    """AI 피드백"""
    __tablename__ = "ai_feedbacks"

    ai_feedback_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_quest_attempt_id = Column(BigInteger, ForeignKey("user_quest_attempts.user_quest_attempt_id"),
                                    nullable=False, comment="사용자 문제 이력 달력 id")
    created_at = Column(TIMESTAMP, comment="AI 생성 날짜")
    message = Column(String(100), comment="학습 요약 메시지")
    detail = Column(String(500), comment="칭찬 메시지")
    tags = Column(String(500), comment="동기부여 메시지")

    # Relationships
    quest_attempts = relationship("UserQuestAttempt", back_populates="ai_feedback")


class Vocabulary(Base):
    """어휘"""
    __tablename__ = "vocabulary"

    vocab_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    str = Column(String(50), nullable=False, comment="문자열")
    url_normal = Column(String(500), nullable=False, comment="일반 url")
    slow_normal = Column(String(500), nullable=False, comment="느린 url")
    created_at = Column(TIMESTAMP, nullable=False)
