from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .storage import new_session, load_session, save_session
from .agents import run_panel_round

app = FastAPI()

# Make sure the frontend folder exists!
app.mount("/static", StaticFiles(directory="frontend"), name="static")

class RunRoundReq(BaseModel):
    session_id: str
    user_prompt: str
    mode: str = "FREESTYLE"
    enabled_agents: list[str] = ["BioExpert", "AIExpert", "Reviewer", "GrantsWriter"]

@app.get("/", response_class=HTMLResponse)
def index():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/new_session")
def api_new_session():
    sid = new_session()
    return {"session_id": sid, "messages": []}

@app.post("/api/run_round")
def api_run_round(req: RunRoundReq):
    history = load_session(req.session_id)
    
    # Run the AutoGen logic
    new_msgs = run_panel_round(
        user_prompt=req.user_prompt,
        mode=req.mode,
        enabled=req.enabled_agents,
        history=history
    )

    # Update and save state
    full_history = history + [{"role": "user", "name": "User", "content": req.user_prompt}] + new_msgs
    save_session(req.session_id, full_history)
    
    return {"messages": full_history}