from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # связи
    cards = relationship("Card", back_populates="owner", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")

class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    foreign_word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    example_sentence = Column(String, nullable=True)
    language = Column(String, default="english")
    difficulty_level = Column(Integer, default=1)  # легкий, средний, сложный
    last_reviewed = Column(DateTime(timezone=True), nullable=True)
    next_review = Column(DateTime(timezone=True), nullable=True)
    correct_answers = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # связи
    owner = relationship("User", back_populates="cards")

class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_type = Column(String, default="test")
    total_cards = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # связи
    user = relationship("User", back_populates="study_sessions")