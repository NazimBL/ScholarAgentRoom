import os
import os
import asyncio
from dotenv import load_dotenv

# Use the newer autogen packages
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage, StructuredMessage

from .prompts import (
    MODERATOR_SYSTEM, EVIDENCE_TEMPLATE,
    BIO_EXPERT_SYSTEM, AI_EXPERT_SYSTEM, REVIEWER_SYSTEM, GRANTSMAN_SYSTEM
)

load_dotenv()

#MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"
MODEL_NAME = "nvidia/Llama-3.1-Nemotron-Nano-8B-v1"

def build_model_client():
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    from autogen_core.models import ModelInfo

    # Check for Gemini/Google usage
    if os.environ.get("GEMINI_API_KEY"):
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        api_key = os.environ["GEMINI_API_KEY"]
        model = "gemini-1.5-flash"
        print(f"--- DETECTED GEMINI_API_KEY: Switching to Google OpenAI Endpoint ({model}) ---")
    else:
        base_url = os.environ.get("LLM_BASE_URL", "http://localhost:8000/v1")
        model = os.environ.get("LLM_MODEL", MODEL_NAME)
        api_key = os.environ.get("LLM_API_KEY", "local-dev-key")

    print(f"--- TACTICAL CHECK: Connecting to {base_url} with model {model} ---")

    return OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
        model_info=ModelInfo(
            vision=False,
            function_calling=True,
            json_output=True,
            family="unknown" # This bypasses the OpenAI-only check
        )
    )


def build_agents(mode: str):
    mode = (mode or "").upper().strip()
    suffix = f"\n\nCRITICAL: EVIDENCE MODE IS ACTIVE.\n{EVIDENCE_TEMPLATE}" if mode == "EVIDENCE" else ""

    model_client = build_model_client()

    moderator = AssistantAgent(
        name="Moderator",
        model_client=model_client,
        system_message=MODERATOR_SYSTEM + suffix,
    )

    bio = AssistantAgent(
        name="BioExpert",
        model_client=model_client,
        system_message=BIO_EXPERT_SYSTEM + suffix,
    )

    ai = AssistantAgent(
        name="AIExpert",
        model_client=model_client,
        system_message=AI_EXPERT_SYSTEM + suffix,
    )

    reviewer = AssistantAgent(
        name="Reviewer",
        model_client=model_client,
        system_message=REVIEWER_SYSTEM + suffix,
    )

    grant = AssistantAgent(
        name="GrantsWriter",
        model_client=model_client,
        system_message=GRANTSMAN_SYSTEM + suffix,
    )

    return moderator, bio, ai, reviewer, grant


def _msg_to_text(msg):
    if isinstance(msg, TextMessage):
        return msg.content
    if isinstance(msg, StructuredMessage):
        return msg.to_text()
    # generic fallback
    return getattr(msg, "content", str(msg))


async def run_panel_round(user_prompt: str, mode: str, enabled: list[str], history: list[dict], max_turns: int = 6):
    """Run a single panel round and return new assistant messages.

    This function is now async to integrate with FastAPI's event loop.
    """
    moderator, bio, ai, reviewer, grant = build_agents(mode)

    name_to_agent = {
        "BioExpert": bio,
        "AIExpert": ai,
        "Reviewer": reviewer,
        "GrantsWriter": grant,
    }

    participants = [moderator]
    for n in enabled or []:
        if n in name_to_agent:
            participants.append(name_to_agent[n])

    # Create the team (round-robin)
    team = RoundRobinGroupChat(participants, max_turns=max_turns)

    # Format history for context
    context = ""
    if history:
        context = "Previous Conversation Context:\n" + "\n".join(
            [f"{m.get('name', m['role'])}: {m['content']}" for m in history[-10:]]
        )

    kickoff_msg = f"{context}\n\nUSER PROMPT: {user_prompt}\n\nModerator, please start the panel discussion."

    # Run the team asynchronously
    result = await team.run(task=kickoff_msg)

    out = []
    for m in result.messages:
        # Only include chat messages (TextMessage / StructuredMessage)
        try:
            name = getattr(m, "source", None) or getattr(m, "name", None) or "assistant"
            content = _msg_to_text(m)
            out.append({"role": "assistant", "name": name, "content": content})
        except Exception:
            # skip non-chat events
            continue

    return out