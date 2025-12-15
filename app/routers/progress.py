from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app import crud, schemas, models
from app.auth import get_current_active_user
from app.database import get_db

router = APIRouter()

@router.get("/", response_model=schemas.ProgressStats)
async def get_progress_stats(
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение статистики прогресса изучения"""
    stats = await crud.get_user_progress_stats(db, user_id=current_user.id)
    return stats

@router.get("/test", response_model=List[schemas.CardResponse])
async def get_test_cards(
    limit: int = 10,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение карточек для тестирования"""
    cards = await crud.get_random_cards_for_user(db, user_id=current_user.id, limit=limit)
    
    if not cards:
        raise HTTPException(
            status_code=404,
            detail="No cards available for testing"
        )
    
    result_cards = []
    for card in cards:
        card_dict = {
            "id": card.id,
            "foreign_word": card.foreign_word,
            "translation": card.translation,
            "example_sentence": card.example_sentence,
            "language": card.language,
            "difficulty_level": card.difficulty_level,
            "created_by": card.created_by,
            "created_at": card.created_at,
            "updated_at": card.updated_at,
        }
        
        progress = await crud.get_user_progress_for_card(db, current_user.id, card.id)
        if progress:
            card_dict["user_progress"] = progress
        
        result_cards.append(card_dict)
    
    return result_cards

@router.post("/test", response_model=schemas.TestResult)
async def submit_test(
    test_data: schemas.TestSubmission,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Отправка результатов теста"""
    correct_answers = 0
    
    for answer in test_data.answers:
        card = await crud.get_card(db, card_id=answer.card_id)
        
        if card:
            is_correct = answer.user_answer.strip().lower() == card.translation.lower()
            
            if is_correct:
                correct_answers += 1
            
            await crud.update_user_progress(
                db, 
                user_id=current_user.id, 
                card_id=card.id, 
                is_correct=is_correct
            )
    
    score_percentage = 0
    if test_data.answers:
        score_percentage = (correct_answers / len(test_data.answers)) * 100
    
    return {
        "total_questions": len(test_data.answers),
        "correct_answers": correct_answers,
        "score_percentage": round(score_percentage, 2)
    }

@router.get("/review", response_model=List[schemas.CardResponse])
async def get_cards_for_review(
    limit: int = 10,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение карточек для повторения."""
    cards = await crud.get_cards_for_user_review(db, user_id=current_user.id, limit=limit)
    
    if not cards:
        raise HTTPException(
            status_code=404,
            detail="No cards need review today"
        )
    
    result_cards = []
    for card in cards:
        card_dict = {
            "id": card.id,
            "foreign_word": card.foreign_word,
            "translation": card.translation,
            "example_sentence": card.example_sentence,
            "language": card.language,
            "difficulty_level": card.difficulty_level,
            "created_by": card.created_by,
            "created_at": card.created_at,
            "updated_at": card.updated_at,
        }
        
        progress = await crud.get_user_progress_for_card(db, current_user.id, card.id)
        if progress:
            card_dict["user_progress"] = progress
        
        result_cards.append(card_dict)
    
    return result_cards