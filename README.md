
## Overview

On this project I experimented building a multi-agent conversational chat system. I use an AutoGen orchestrator to run expert-level brainstorming sessions, bringing together specialized AI agents (a Biology expert, AI engineer, scientific reviewer, and a grant writer) to battle-test research proposals and simulate high-stakes scientific panel (Evidence mode), or a more relaxed brainstorming session (Freestyle mode).

### Key Features

- **Multi-Expert Coordination**: Four specialized agents with focused system prompts
  - **BioExpert**: Mechanistic plausibility & experimental feasibility
  - **AIExpert**: Data requirements, modeling, and evaluation
  - **Reviewer**: Critical feedback (NIH-style rigor)
  - **GrantsWriter**: Clarity, significance, and innovation framing
  - **Moderator**: Panel orchestration and summary
  
- **Dual Modes**:
  - **Freestyle**: Open-ended discussion
  - **Evidence Mode**: Agents must structure critiques with claim–evidence–risk–improvement–confidence framework
  
- **Session Persistence**: Conversations stored in JSON, allowing multi-turn interactions
- **Interactive Web UI**: Real-time chat interface with agent toggle controls
- **Scalable Backend**: FastAPI + asyncio for handling concurrent agent runs

---

###  Workflow

1. **Create New Session**: Click "New Session" to initialize a conversation thread.
2. **Configure Agents**: Toggle desired agents (BioExpert, AIExpert, Reviewer, GrantsWriter).
3. **Select Mode**: Choose **Freestyle** or **Evidence-based** (forces structured critique format).
4. **Submit Prompt**: Paste research idea or grant abstract and click **Run Panel Round**.
5. **Review Output**: Agents deliberate in round-robin; messages stream live to chat panel.
6. **Multi-Turn**: Continue discussing; history is retained per session.

### Interface Overview

![Agent Response 1](screenshots/agentroom1.png)

*Example: Agents discussing research methodology with structured feedback.*

![Agent Response 2](screenshots/agentroom2.png)

*Real-time agent deliberation in evidence-based mode.*

![Panel Discussion](screenshots/agentroom3.png)

*Multi-turn conversation with full history preservation.*

---

## System Architecture Diagram
I deployed this to a GPU-accelerated cluster accessed securely via SSH tunnel:

```
┌─────────────────────────────────────────────────────────────┐
│                       User Browser                           │
│  (Frontend: Vue-like JS + CSS Grid Chat Interface)           │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP/JSON
         ┌─────────▼─────────┐
         │  SSH Tunnel       │
         │  :8000 (Local)    │  ◄─── Secure Remote Access
         └─────────┬─────────┘
                   │
      ┌────────────▼─────────────────┐
      │    Remote Cluster Nodes       │
      │  (FastAPI + Uvicorn Server)   │
      │  :8000                        │
      │                               │
      │  ┌─────────────────────────┐  │
      │  │  AutoGen Team            │  │
      │  │  - RoundRobinGroupChat   │  │
      │  │  - AssistantAgents       │  │
      │  │  - Message Flow          │  │
      │  └──────────┬──────────────┘  │
      │             │                  │
      │             ▼                  │
      │  ┌─────────────────────────┐  │
      │  │  LLM Inference (GPU)      │  │
      │  │  OpenAI Client /          │  │
      │  │  Local VLLM Server        │  │
      │  │                           │  │
      │  └─────────────────────────┘  │
      └───────────────────────────────┘
```

---

### Agent System Prompts

Defined in `backend/prompts.py`:

- **MODERATOR_SYSTEM**: Controls discussion flow, ensures constructive & non-repetitive feedback, generates panel summaries.
- **BIO_EXPERT_SYSTEM**: Focus on mechanistic plausibility and experimental feasibility.
- **AI_EXPERT_SYSTEM**: Data requirements, modeling choices, evaluation methodology.
- **REVIEWER_SYSTEM**: NIH-style critical reviewer lens; identifies weaknesses and missing controls.
- **GRANTSMAN_SYSTEM**: Clarity, innovation framing, and significance for funding bodies.

**Evidence Mode Template** (`EVIDENCE_TEMPLATE`):
```
1) Claim (what you're critiquing)
2) Evidence (domain principle or data)
3) Risk / failure mode
4) Concrete improvement
5) Confidence (High/Med/Low)
```
## Project Structure

```
agentroom/
├── backend/
│   ├── app.py              # FastAPI application & routes
│   ├── agents.py           # AutoGen agent builders & run logic
│   ├── prompts.py          # System messages & EVIDENCE_TEMPLATE
│   ├── storage.py          # Session JSON I/O
│   └── __init__.py
├── frontend/
│   ├── index.html          # Chat UI (HTML + embedded CSS)
│   └── app.js              # Client-side JavaScript logic
├── sessions/               # Persisted conversation JSON
├── screenshots/            # Portfolio images
├── pyproject.toml          # Project metadata & dependencies
├── .env                    # LLM credentials (not committed)
└── README.md               # This file
```

## Future Enhancements

- [ ] **Streaming Responses**: Real-time token streaming from LLM to UI
- [ ] **Custom Agent Roles**: Allow users to define custom agent personas
- [ ] **Export Reports**: Generate PDF summaries of panel discussions
- [ ] **Agent Memory**: Long-term context & knowledge base integration
- [ ] **Web-Based Editor**: Define system prompts on-the-fly in UI
- [ ] **Team Variants**: Swarm behavior, hierarchical decision-making
- [ ] **Database Backend**: Replace JSON sessions with PostgreSQL for scale

---

## Contact & Questions

For questions or collaboration inquiries, please reach out.
