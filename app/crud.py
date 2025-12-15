from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select, update, delete, or_
from typing import List, Optional
from datetime import datetime, timedelta
import random

from app import models, schemas
from app.auth import get_password_hash

# Пользователи
async def get_user(db: AsyncSession, user_id: int) -> Optional[models.User]:
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
    result = await db.execute(
        select(models.User).where(models.User.username == username)
    )
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    result = await db.execute(
        select(models.User).where(models.User.email == email)
    )
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# Карточки
async def get_card(db: AsyncSession, card_id: int) -> Optional[models.Card]:
    result = await db.execute(
        select(models.Card).where(models.Card.id == card_id)
    )
    return result.scalar_one_or_none()

async def get_all_cards(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Card]:
    """Получить все карточки"""
    result = await db.execute(
        select(models.Card)
        .order_by(models.Card.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def create_card(db: AsyncSession, card: schemas.CardCreate, admin_id: int) -> models.Card:
    """Создать карточку"""
    db_card = models.Card(
        **card.dict(),
        created_by=admin_id
    )
    db.add(db_card)
    await db.commit()
    await db.refresh(db_card)
    return db_card

async def update_card(
    db: AsyncSession, 
    card_id: int, 
    card_update: schemas.CardUpdate
) -> Optional[models.Card]:
    """Обновить карточку"""
    result = await db.execute(
        select(models.Card).where(models.Card.id == card_id)
    )
    db_card = result.scalar_one_or_none()
    
    if not db_card:
        return None
    
    update_data = card_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_card, field, value)
    
    db_card.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_card)
    return db_card

async def delete_card(db: AsyncSession, card_id: int) -> bool:
    """Удалить карточку"""
    result = await db.execute(
        select(models.Card).where(models.Card.id == card_id)
    )
    db_card = result.scalar_one_or_none()
    
    if not db_card:
        return False
    
    await db.delete(db_card)
    await db.commit()
    return True

# Прогресс
async def get_or_create_user_progress(
    db: AsyncSession, 
    user_id: int, 
    card_id: int
) -> Optional[models.UserCardProgress]:
    """Получить или создать прогресс пользователя по карточке"""
    try:
        result = await db.execute(
            select(models.UserCardProgress).where(
                and_(
                    models.UserCardProgress.user_id == user_id,
                    models.UserCardProgress.card_id == card_id
                )
            )
        )
        progress = result.scalar_one_or_none()
        
        if not progress:
            progress = models.UserCardProgress(
                user_id=user_id,
                card_id=card_id,
                next_review=datetime.utcnow()
            )
            db.add(progress)
            await db.commit()
            await db.refresh(progress)
        
        return progress
    except Exception as e:
        print(f"Error in get_or_create_user_progress: {e}")
        return None

async def update_user_progress(
    db: AsyncSession, 
    user_id: int, 
    card_id: int, 
    is_correct: bool
) -> Optional[models.UserCardProgress]:
    """Обновить прогресс пользователя по карточке"""
    progress = await get_or_create_user_progress(db, user_id, card_id)
    
    if not progress:
        return None
    
    progress.total_attempts += 1
    if is_correct:
        progress.correct_answers += 1
    
    progress.last_reviewed = datetime.utcnow()
    
    if is_correct:
        interval_days = min(30, 2 ** min(progress.correct_answers, 5))
    else:
        interval_days = 1
    
    progress.next_review = datetime.utcnow() + timedelta(days=interval_days)
    progress.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(progress)
    return progress

async def get_user_progress_for_card(
    db: AsyncSession,
    user_id: int,
    card_id: int
) -> Optional[dict]:
    """Получить прогресс пользователя по конкретной карточке"""
    result = await db.execute(
        select(models.UserCardProgress).where(
            and_(
                models.UserCardProgress.user_id == user_id,
                models.UserCardProgress.card_id == card_id
            )
        )
    )
    progress = result.scalar_one_or_none()
    
    if progress:
        return {
            "correct_answers": progress.correct_answers,
            "total_attempts": progress.total_attempts,
            "last_reviewed": progress.last_reviewed,
            "next_review": progress.next_review
        }
    return None

async def get_cards_for_user_review(
    db: AsyncSession, 
    user_id: int, 
    limit: int = 10
) -> List[models.Card]:
    """Получить карточки для повторения пользователем."""
    now = datetime.utcnow()
    
    query = select(models.Card).join(
        models.UserCardProgress,
        and_(
            models.UserCardProgress.card_id == models.Card.id,
            models.UserCardProgress.user_id == user_id
        ),
        isouter=True
    ).where(
        or_(
            models.UserCardProgress.id == None,
            models.UserCardProgress.next_review <= now
        )
    ).order_by(
        models.UserCardProgress.next_review.asc().nullsfirst()
    ).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_random_cards_for_user(
    db: AsyncSession, 
    user_id: int, 
    limit: int = 10
) -> List[models.Card]:
    """Получить случайные карточки для теста пользователя"""
    result = await db.execute(select(models.Card))
    all_cards = result.scalars().all()
    
    if not all_cards:
        return []
    
    weighted_cards = []
    
    for card in all_cards:
        progress_result = await db.execute(
            select(models.UserCardProgress).where(
                and_(
                    models.UserCardProgress.user_id == user_id,
                    models.UserCardProgress.card_id == card.id
                )
            )
        )
        progress = progress_result.scalar_one_or_none()
        
        attempts = progress.total_attempts if progress else 0
        weight = 10 / (attempts + 1)
        
        weighted_cards.extend([card] * int(weight))
    
    if not weighted_cards:
        return random.sample(all_cards, min(limit, len(all_cards)))
    
    return random.sample(weighted_cards, min(limit, len(weighted_cards)))

# Статистика
async def get_user_progress_stats(db: AsyncSession, user_id: int) -> dict:
    """Получить статистику прогресса пользователя"""
    total_cards_query = select(func.count(models.Card.id))
    total_cards_result = await db.execute(total_cards_query)
    total_cards = total_cards_result.scalar() or 0
    
    
    total_reviews_query = select(func.sum(models.UserCardProgress.total_attempts)).where(
        models.UserCardProgress.user_id == user_id
    )
    total_reviews_result = await db.execute(total_reviews_query)
    total_reviews = total_reviews_result.scalar() or 0
    
    total_correct_query = select(func.sum(models.UserCardProgress.correct_answers)).where(
        models.UserCardProgress.user_id == user_id
    )
    total_correct_result = await db.execute(total_correct_query)
    total_correct = total_correct_result.scalar() or 0
    
    average_score = 0
    if total_reviews > 0:
        average_score = (total_correct / total_reviews) * 100
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    activity_days_query = select(
        func.date(models.UserCardProgress.last_reviewed)
    ).where(
        and_(
            models.UserCardProgress.user_id == user_id,
            models.UserCardProgress.last_reviewed >= week_ago
        )
    ).distinct()
    
    activity_days_result = await db.execute(activity_days_query)
    activity_days = len(set([row[0] for row in activity_days_result.all() if row[0]]))
    
    return {
        "total_cards": total_cards,
        "total_reviews": total_reviews,
        "average_score": round(average_score, 2),
        "streak_days": activity_days
    }