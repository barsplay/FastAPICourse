from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import random

from app import models, schemas
from app.auth import get_password_hash

# пользователи
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# карточки
def get_card(db: Session, card_id: int):
    return db.query(models.Card).filter(models.Card.id == card_id).first()

def get_user_cards(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Card).filter(
        models.Card.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_cards_for_review(db: Session, user_id: int, limit: int = 10):
    """Карточки для повторения"""
    now = datetime.utcnow()
    return db.query(models.Card).filter(
        and_(
            models.Card.user_id == user_id,
            models.Card.next_review <= now
        )
    ).limit(limit).all()

def get_random_cards(db: Session, user_id: int, limit: int = 10):
    """Получение карточек для теста"""
    cards = db.query(models.Card).filter(
        models.Card.user_id == user_id
    ).all()
    
    if not cards:
        return []
    
    weighted_cards = []
    for card in cards:
        weight = 1 / (card.total_attempts + 1)
        weighted_cards.extend([card] * int(weight * 10))
    
    return random.sample(weighted_cards, min(limit, len(weighted_cards)))

def create_card(db: Session, card: schemas.CardCreate, user_id: int):
    db_card = models.Card(
        **card.dict(),
        user_id=user_id
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

def update_card(db: Session, card_id: int, card_update: schemas.CardUpdate, user_id: int):
    db_card = get_card(db, card_id)
    
    if not db_card:
        return None
    
    if db_card.user_id != user_id:
        return None
    
    update_data = card_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_card, field, value)
    
    db.commit()
    db.refresh(db_card)
    return db_card

def delete_card(db: Session, card_id: int, user_id: int):
    db_card = get_card(db, card_id)
    
    if not db_card:
        return False
    
    if db_card.user_id != user_id:
        return False
    
    db.delete(db_card)
    db.commit()
    return True

def update_card_progress(db: Session, card_id: int, is_correct: bool):
    """Обновление прогресса карточки"""
    db_card = get_card(db, card_id)
    
    if not db_card:
        return None
    
    db_card.total_attempts += 1
    if is_correct:
        db_card.correct_answers += 1
    
    db_card.last_reviewed = datetime.utcnow()
    
    if is_correct:
        interval_days = min(30, 2 ** min(db_card.correct_answers, 5))
    else:
        interval_days = 1
    
    db_card.next_review = datetime.utcnow() + timedelta(days=interval_days)
    
    db.commit()
    db.refresh(db_card)
    return db_card

# сессии изучения
def create_study_session(db: Session, session_data: schemas.StudySessionCreate, user_id: int):
    db_session = models.StudySession(
        **session_data.dict(),
        user_id=user_id
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_user_progress_stats(db: Session, user_id: int):
    """Статистика прогресса пользователя"""
    from sqlalchemy import func
    
    total_cards = db.query(func.count(models.Card.id)).filter(
        models.Card.user_id == user_id
    ).scalar() or 0
    
    cards_for_today = db.query(func.count(models.Card.id)).filter(
        and_(
            models.Card.user_id == user_id,
            models.Card.next_review <= datetime.utcnow()
        )
    ).scalar() or 0
    
    total_reviews = db.query(func.sum(models.Card.total_attempts)).filter(
        models.Card.user_id == user_id
    ).scalar() or 0
    
    total_correct = db.query(func.sum(models.Card.correct_answers)).filter(
        models.Card.user_id == user_id
    ).scalar() or 0
    
    average_score = 0
    if total_reviews > 0:
        average_score = (total_correct / total_reviews) * 100
    
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_sessions = db.query(models.StudySession).filter(
        and_(
            models.StudySession.user_id == user_id,
            models.StudySession.completed_at >= seven_days_ago
        )
    ).count()
    
    streak_days = min(recent_sessions, 7)
    
    return {
        "total_cards": total_cards,
        "cards_today": cards_for_today,
        "total_reviews": total_reviews,
        "average_score": round(average_score, 2),
        "streak_days": streak_days
    }