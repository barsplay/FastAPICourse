from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app import crud, schemas, models
from app.auth import get_current_active_user, require_admin
from app.database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.CardResponse])
async def get_all_cards(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все карточки"""
    cards = await crud.get_all_cards(db, skip=skip, limit=limit)
    
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

@router.get("/{card_id}", response_model=schemas.CardResponse)
async def get_card(
    card_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить конкретную карточку"""
    card = await crud.get_card(db, card_id=card_id)
    
    if not card:
        raise HTTPException(
            status_code=404,
            detail="Card not found"
        )
    
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
    
    return card_dict

@router.post("/", response_model=schemas.CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    card_data: schemas.CardCreate,
    current_user: models.User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Создать новую карточку"""
    return await crud.create_card(db=db, card=card_data, admin_id=current_user.id)

@router.put("/{card_id}", response_model=schemas.CardResponse)
async def update_card(
    card_id: int,
    card_update: schemas.CardUpdate,
    current_user: models.User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Обновить карточку"""
    card = await crud.update_card(db, card_id=card_id, card_update=card_update)
    
    if not card:
        raise HTTPException(
            status_code=404,
            detail="Card not found"
        )
    
    return card

@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: int,
    current_user: models.User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Удалить карточку"""
    success = await crud.delete_card(db, card_id=card_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Card not found"
        )