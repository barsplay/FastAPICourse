from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.auth import get_current_active_user
from app.database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.CardResponse])
async def read_user_cards(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # получение всех карточек пользователя
    cards = crud.get_user_cards(
        db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit
    )
    return cards

@router.get("/{card_id}", response_model=schemas.CardResponse)
async def read_card(
    card_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # получение карточки по id
    card = crud.get_card(db, card_id=card_id)
    
    if not card:
        raise HTTPException(
            status_code=404,
            detail="Card not found"
        )
    
    if card.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    return card

@router.post("/", response_model=schemas.CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    card_data: schemas.CardCreate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # создание карточки
    return crud.create_card(
        db=db, 
        card=card_data, 
        user_id=current_user.id
    )

@router.put("/{card_id}", response_model=schemas.CardResponse)
async def update_card(
    card_id: int,
    card_update: schemas.CardUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # обновление карточки
    card = crud.update_card(
        db=db, 
        card_id=card_id, 
        card_update=card_update, 
        user_id=current_user.id
    )
    
    if not card:
        raise HTTPException(
            status_code=404,
            detail="Card not found or you don't have permission"
        )
    
    return card

@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # удаление карточки
    success = crud.delete_card(db, card_id=card_id, user_id=current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Card not found or you don't have permission"
        )