import uuid
from .db import async_session, SessionModel
from sqlalchemy import select

def new_session() -> str:
    """Create a new session ID (UUID)."""
    return str(uuid.uuid4())[:8]

async def load_session(session_id: str) -> list[dict]:
    """Load session history from database."""
    async with async_session() as db:
        result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
        session_obj = result.scalar_one_or_none()
        if session_obj:
            return session_obj.messages
        return []

async def save_session(session_id: str, messages: list[dict]) -> None:
    """Save session history to database (Upsert)."""
    async with async_session() as db:
        result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
        session_obj = result.scalar_one_or_none()
        
        if session_obj:
            session_obj.messages = messages
        else:
            session_obj = SessionModel(id=session_id, messages=messages)
            db.add(session_obj)
        
        await db.commit()