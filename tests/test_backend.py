
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from backend.app import app
from backend.db import init_db, async_session, SessionModel
from sqlalchemy import select

# Configure the async client fixture
@pytest.fixture(scope="function")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# Database setup fixture
@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    """Reset DB before each test."""
    await init_db()
    yield

@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "AgentRoom" in response.text

@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post("/api/new_session")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) == 8
    
    # Verify DB persistence
    sid = data["session_id"]
    async with async_session() as db:
        result = await db.execute(select(SessionModel).where(SessionModel.id == sid))
        session_obj = result.scalar_one_or_none()
        assert session_obj is not None
        assert session_obj.id == sid

@pytest.mark.asyncio
async def test_run_round_mocked(client):
    """Test the run_round endpoint with mocked AutoGen agents."""
    
    # Create a session first
    res_new = await client.post("/api/new_session")
    sid = res_new.json()["session_id"]
    
    # Mock the run_panel_round function in agents.py
    with patch("backend.app.run_panel_round", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = [
            {"role": "assistant", "name": "BioExpert", "content": "Mocked bio analysis."},
            {"role": "assistant", "name": "Reviewer", "content": "Mocked critique."}
        ]
        
        payload = {
            "session_id": sid,
            "user_prompt": "Test research idea",
            "mode": "FREESTYLE",
            "enabled_agents": ["BioExpert"]
        }
        
        response = await client.post("/api/run_round", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        messages = data["messages"]
        
        # Verify response structure
        assert len(messages) >= 3 
        assert messages[-2]["content"] == "Mocked bio analysis."
        
        mock_run.assert_called_once()

@pytest.mark.asyncio
async def test_history_persistence(client):
    """Verify history endpoint returns saved messages."""
    # 1. Create Session
    res_new = await client.post("/api/new_session")
    sid = res_new.json()["session_id"]
    
    # 2. Add some history via run_round (mocked)
    with patch("backend.app.run_panel_round", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = [{"role": "assistant", "name": "AI", "content": "Stored msg"}]
        await client.post("/api/run_round", json={"session_id": sid, "user_prompt": "save me"})
        
    # 3. Fetch History
    res_hist = await client.get(f"/api/history/{sid}")
    assert res_hist.status_code == 200
    hist_data = res_hist.json()["messages"]
    
    # Check if "Stored msg" is in history
    assert any(m["content"] == "Stored msg" for m in hist_data)

@pytest.mark.asyncio
async def test_invalid_input(client):
    """Test validation."""
    response = await client.post("/api/run_round", json={
        "session_id": "fake",
        "user_prompt": "" # Empty prompt should fail validation
    })
    assert response.status_code == 422
