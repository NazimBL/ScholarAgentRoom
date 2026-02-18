import structlog

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field

from .storage import new_session, load_session, save_session
from .agents import run_panel_round


# --- Logging Setup ---
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

import os
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup_check_start")
    
    # Initialize DB
    await init_db()
    logger.info("db_initialized")
    
    # Check for LLM credentials
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("LLM_API_KEY")
    base_url = os.environ.get("LLM_BASE_URL")
    
    if not gemini_key and not openai_key:
        logger.error("startup_config_error", detail="No API Key found. Set GEMINI_API_KEY or LLM_API_KEY.")
        
    if gemini_key:
        logger.info("startup_config_ok", provider="Gemini")
    elif openai_key:
        logger.info("startup_config_ok", provider="OpenAI/Local", base_url=base_url)
    
    yield
    
    # Shutdown logic (if any)
    logger.info("shutdown")

app = FastAPI(lifespan=lifespan)

# Make sure the frontend folder exists!
app.mount("/static", StaticFiles(directory="frontend"), name="static")


class RunRoundReq(BaseModel):
    session_id: str
    user_prompt: str = Field(..., min_length=1, description="Research idea or prompt cannot be empty")
    mode: str = "FREESTYLE"
    enabled_agents: list[str] = ["BioExpert", "AIExpert", "Reviewer", "GrantsWriter"]

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/new_session")
async def api_new_session():
    sid = new_session()
    await save_session(sid, [])
    logger.info("session_created", session_id=sid)
    return {"session_id": sid, "messages": []}

@app.get("/api/history/{session_id}")
async def api_get_history(session_id: str):
    history = await load_session(session_id)
    if not history and session_id != "null": 
        # minimal check, though load_session returns [] if not found
        pass
    return {"messages": history}

@app.post("/api/run_round")
async def api_run_round(req: RunRoundReq):
    log = logger.bind(session_id=req.session_id, mode=req.mode)
    log.info("run_round_start", prompt_len=len(req.user_prompt))

    history = await load_session(req.session_id)
    
    try:
        # Run the AutoGen logic
        new_msgs = await run_panel_round(
            user_prompt=req.user_prompt,
            mode=req.mode,
            enabled=req.enabled_agents,
            history=history
        )
    except Exception as e:
        log.error("run_round_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

    # Update and save state
    full_history = history + [{"role": "user", "name": "User", "content": req.user_prompt}] + new_msgs
    await save_session(req.session_id, full_history)
    
    log.info("run_round_complete", new_msgs_count=len(new_msgs))
    return {"messages": full_history}