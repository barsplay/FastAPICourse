from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.auth import get_current_active_user
from app.database import get_db

router = APIRouter()

@router.get("/", response_model=schemas.ProgressStats)
async def get_progress_stats(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # получение прогресса изучения
    stats = crud.get_user_progress_stats(db, user_id=current_user.id)
    return stats

@router.get("/test", response_model=List[schemas.CardResponse])
async def get_test_cards(
    limit: int = 10,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # получение теста
    cards = crud.get_random_cards(db, user_id=current_user.id, limit=limit)
    
    if not cards:
        raise HTTPException(
            status_code=404,
            detail="No cards available for testing"
        )
    
    return cards

@router.post("/test", response_model=schemas.TestResult)
async def submit_test(
    test_data: schemas.TestSubmission,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # отправление результатов теста
    correct_answers = 0
    
    for answer in test_data.answers:
        card = crud.get_card(db, card_id=answer.card_id)
        
        if card and card.user_id == current_user.id:

            is_correct = answer.user_answer.strip().lower() == card.translation.lower()
            answer.is_correct = is_correct
            
            if is_correct:
                correct_answers += 1
            
            crud.update_card_progress(db, card_id=card.id, is_correct=is_correct)
    
    # новая сессия обучения
    session_data = schemas.StudySessionCreate(
        session_type="test",
        total_cards=len(test_data.answers),
        correct_answers=correct_answers,
        duration_seconds=test_data.duration_seconds
    )
    
    session = crud.create_study_session(
        db, 
        session_data=session_data, 
        user_id=current_user.id
    )
    
    score_percentage = 0
    if test_data.answers:
        score_percentage = (correct_answers / len(test_data.answers)) * 100
    
    return {
        "total_questions": len(test_data.answers),
        "correct_answers": correct_answers,
        "score_percentage": round(score_percentage, 2),
        "session_id": session.id
    }

@router.get("/review", response_model=List[schemas.CardResponse])
async def get_cards_for_review(
    limit: int = 10,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # карточки на повторение
    cards = crud.get_cards_for_review(db, user_id=current_user.id, limit=limit)
    
    if not cards:
        raise HTTPException(
            status_code=404,
            detail="No cards need review today"
        )
    
    return cards