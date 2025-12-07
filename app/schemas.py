from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CardBase(BaseModel):
    foreign_word: str
    translation: str
    example_sentence: Optional[str] = None
    language: str = "english"
    difficulty_level: int = 1

class CardCreate(CardBase):
    pass

class CardUpdate(BaseModel):
    foreign_word: Optional[str] = None
    translation: Optional[str] = None
    example_sentence: Optional[str] = None
    language: Optional[str] = None
    difficulty_level: Optional[int] = None

class CardResponse(CardBase):
    id: int
    user_id: int
    correct_answers: int
    total_attempts: int
    last_reviewed: Optional[datetime]
    next_review: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class StudySessionBase(BaseModel):
    session_type: str = "test"
    total_cards: int = 0
    correct_answers: int = 0
    duration_seconds: int = 0

class StudySessionCreate(StudySessionBase):
    pass

class StudySessionResponse(StudySessionBase):
    id: int
    user_id: int
    completed_at: datetime
    
    class Config:
        from_attributes = True

class ProgressStats(BaseModel):
    total_cards: int
    cards_today: int
    total_reviews: int
    average_score: float
    streak_days: int

class TestAnswer(BaseModel):
    card_id: int
    user_answer: str
    is_correct: Optional[bool] = None

class TestSubmission(BaseModel):
    answers: List[TestAnswer]
    duration_seconds: int

class TestResult(BaseModel):
    total_questions: int
    correct_answers: int
    score_percentage: float
    session_id: int