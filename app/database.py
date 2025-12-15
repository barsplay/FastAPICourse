from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        future=True,
        poolclass=NullPool,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        future=True,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Создание таблиц и администратора"""
    from sqlalchemy import select
    from app import models
    from app.auth import get_password_hash
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created")
    
    # создание администратора
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(models.User).where(models.User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            admin_user = models.User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash(admin_password),
                role="admin",
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            print("✅ Admin user created: admin")

async def close_db():
    await engine.dispose()
    print("✅ Database connections closed")