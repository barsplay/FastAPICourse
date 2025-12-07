from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import engine, Base, get_db
from app.routers import auth, cards, progress
from sqlalchemy.orm import Session
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    yield

    print("Shutting down")

app = FastAPI(
    title="Foreign Words API",
    description="API для изучения иностранных слов с карточками и тестами",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# роутеры
app.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
app.include_router(cards.router, prefix="/cards", tags=["Карточки"])
app.include_router(progress.router, prefix="/progress", tags=["Прогресс"])

@app.get("/")
async def root():
    return {
        "message": "Добро пожаловать в API для изучения иностранных слов!",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Тест базы данных"""
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)