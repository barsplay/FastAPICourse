from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from pydantic import BaseModel

from app import crud, schemas
from app.auth import (
    verify_password, create_access_token, 
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.database import get_db

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    db_user = await crud.get_user_by_username(db, username=user_data.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    db_user = await crud.get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    user = await crud.create_user(db=db, user=user_data)
    return user

@router.post("/login", response_model=schemas.Token)
async def oauth2_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    return await _perform_login(form_data.username, form_data.password, db)

async def _perform_login(username: str, password: str, db: AsyncSession):
    user = await crud.get_user_by_username(db, username=username)
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds())
    }

@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    return current_user