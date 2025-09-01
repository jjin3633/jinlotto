from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean
from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta

from .session import Base


def kst_now():
    """한국 시간(KST) 기준 현재 시간 반환 (timezone-naive로 저장)"""
    kst_time = datetime.now(timezone(timedelta(hours=9)))
    # Supabase에서는 timezone-naive datetime을 저장하므로 timezone 정보 제거
    return kst_time.replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    user_key = Column(String(64), primary_key=True, index=True)
    created_at = Column(DateTime, default=kst_now, nullable=False)

    predictions = relationship("Prediction", back_populates="user")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_key = Column(String(64), ForeignKey("users.user_key"), nullable=False, index=True)
    generated_for = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=kst_now, nullable=False, index=True)
    set_index = Column(Integer, nullable=False)
    numbers = Column(JSON, nullable=False)  # [n1..n6]
    source = Column(String(32), default="daily-fixed", nullable=False)

    user = relationship("User", back_populates="predictions")
    matches = relationship("Match", back_populates="prediction")


class Draw(Base):
    __tablename__ = "draws"

    draw_number = Column(Integer, primary_key=True)
    draw_date = Column(Date, nullable=False)
    numbers = Column(JSON, nullable=False)
    bonus_number = Column(Integer, nullable=False)


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False, index=True)
    draw_number = Column(Integer, nullable=False, index=True)
    match_count = Column(Integer, nullable=False)
    bonus_match = Column(Boolean, default=False, nullable=False)
    rank = Column(Integer, nullable=False)
    matched_numbers = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=kst_now, nullable=False)

    prediction = relationship("Prediction", back_populates="matches")


