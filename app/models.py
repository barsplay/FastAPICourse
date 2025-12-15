from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    foreign_word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    example_sentence = Column(String, nullable=True)
    language = Column(String, default="english")
    difficulty_level = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UserCardProgress(Base):
    """Прогресс конкретного пользователя по конкретной карточке"""
    __tablename__ = "user_card_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    correct_answers = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    last_reviewed = Column(DateTime(timezone=True), nullable=True)
    next_review = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'card_id', name='unique_user_card'),
    )