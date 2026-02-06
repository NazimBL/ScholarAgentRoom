import json
import os
import uuid
from pathlib import Path

# Look for sessions folder in the root
SESS_DIR = Path(__file__).resolve().parent.parent / "sessions"
SESS_DIR.mkdir(parents=True, exist_ok=True)

def new_session() -> str:
    sid = str(uuid.uuid4())[:8] # Short ID for easier tracking
    save_session(sid, [])
    return sid

def load_session(session_id: str) -> list[dict]:
    path = SESS_DIR / f"{session_id}.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_session(session_id: str, messages: list[dict]) -> None:
    path = SESS_DIR / f"{session_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)