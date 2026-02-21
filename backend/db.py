import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON, String
from typing import List, Dict, Any

# Default to SQLite, allow override for Postgres
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./sessions.db")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    messages: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_session():
    async with async_session() as session:
        yield session
