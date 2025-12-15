from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db, close_db
from app.routers import auth, cards, progress
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Foreign Words API...")
    
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    
    yield
    
    print("🛑 Shutting down...")
    await close_db()
    print("✅ Database connections closed")

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

app.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
app.include_router(cards.router, prefix="/cards", tags=["Карточки"])
app.include_router(progress.router, prefix="/progress", tags=["Прогресс"])

@app.get("/")
async def root():
    return {
        "message": "Добро пожаловать в API для изучения иностранных слов!",
        "docs": "/docs",
        "admin": "Login as 'admin' to manage cards"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)