import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import openai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from foundry_local import FoundryLocalManager
from dotenv import load_dotenv
import yaml

from tool import get_current_time

load_dotenv()


FOUNDRY_LOCAL_MODEL_NAME = os.getenv("FOUNDRY_LOCAL_MODEL_NAME") or "qwen2.5-7b-instruct-qnn-npu:2"

AGENT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "agent.yaml")
DEFAULT_SYSTEM_PROMPT = "You are a personal assistant."
TOOL_SYSTEM_PROMPT = (
    "If the user asks for the current time, you must call the get_current_time tool. "
    "Do not answer the time directly without calling the tool."
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("foundry_api")


def _load_agent_config() -> dict[str, Any]:
    try:
        with open(AGENT_CONFIG_PATH, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
            return data
    except FileNotFoundError:
        logger.warning("agent.yaml not found at %s. Using default system prompt.", AGENT_CONFIG_PATH)
        return {}
    except Exception as exc:
        logger.exception("Failed to load agent.yaml: %s", exc)
        return {}

def _get_system_prompt() -> tuple[str, str]:
    config = _load_agent_config()
    agent = config.get("agent", {}) if isinstance(config, dict) else {}
    name = agent.get("name") if isinstance(agent, dict) else None
    prompt = agent.get("system_prompt") if isinstance(agent, dict) else None
    base_prompt = prompt or DEFAULT_SYSTEM_PROMPT
    return (name or "agent", f"{base_prompt}\n\n{TOOL_SYSTEM_PROMPT}")


def _looks_like_time_request(messages: list[dict[str, Any]]) -> bool:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = (message.get("content") or "").lower()
            return "time" in content or "current time" in content
    return False


class ChatRequest(BaseModel):
    messages: list[dict[str, Any]]
    model: str | None = None


class ChatResponse(BaseModel):
    reply: str


class AgentResponse(BaseModel):
    name: str
    system_prompt: str


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        logger.info("Preloading model on startup using FOUNDRY_LOCAL_MODEL_NAME=%s", FOUNDRY_LOCAL_MODEL_NAME)
        _ensure_ready(FOUNDRY_LOCAL_MODEL_NAME)
    except Exception as exc:
        logger.exception("Failed to preload model on startup: %s", exc)
    yield


app = FastAPI(title="Foundry Local Chat API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_manager: FoundryLocalManager | None = None
_client: openai.OpenAI | None = None
_model_id: str | None = None


def _ensure_ready(model_alias: str) -> None:
    global _manager, _client, _model_id
    if _manager is None:
        logger.info("Starting Foundry Local service for model alias: %s", model_alias)
        _manager = FoundryLocalManager(model_alias)
    if _model_id is None or _client is None:
        _model_id = _manager.get_model_info(model_alias).id
        logger.info("Using model id: %s", _model_id)
        _client = openai.OpenAI(
            base_url=_manager.endpoint,
            api_key=_manager.api_key,
        )
        logger.info("OpenAI client ready at endpoint: %s", _manager.endpoint)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/agent", response_model=AgentResponse)
def agent() -> AgentResponse:
    name, prompt = _get_system_prompt()
    return AgentResponse(name=name, system_prompt=prompt)


def _safe_parse_function_args(raw_args: str | None) -> dict[str, Any]:
    if not raw_args:
        return {}
    try:
        return json.loads(raw_args)
    except json.JSONDecodeError:
        logger.warning("Failed to parse function_call.arguments: %s", raw_args)
        return {}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    model_alias = request.model or FOUNDRY_LOCAL_MODEL_NAME
    try:
        logger.info("Chat request received. model_alias=%s messages=%d", model_alias, len(request.messages))
        _ensure_ready(model_alias)
        agent_name, system_prompt = _get_system_prompt()
        logger.info("Using agent config: %s", agent_name)
        functions = [
            {
                "name": "get_current_time",
                "description": "Get the current local system time.",
                "parameters": {"type": "object", "properties": {}},
            }
        ]

        request_messages = [{"role": "system", "content": system_prompt}, *request.messages]
        response = _client.chat.completions.create(
            model=_model_id,
            messages=request_messages,
            functions=functions,
            function_call="auto",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    assistant_message = response.choices[0].message
    function_call = assistant_message.function_call

    if function_call:
        if function_call.name != "get_current_time":
            raise HTTPException(status_code=400, detail=f"Unknown function: {function_call.name}")
        _safe_parse_function_args(function_call.arguments)
        result = get_current_time()
        logger.info("Executed function get_current_time -> %s", result)

        followup_messages = list(request_messages)
        followup_messages.append(assistant_message)
        followup_messages.append(
            {
                "role": "function",
                "name": function_call.name,
                "content": json.dumps({"result": result}),
            }
        )

        response = _client.chat.completions.create(
            model=_model_id,
            messages=followup_messages,
        )
        assistant_message = response.choices[0].message
    elif _looks_like_time_request(request.messages):
        result = get_current_time()
        logger.info("Fallback time tool -> %s", result)
        return ChatResponse(reply=f"The current local time is {result}.")

    reply = assistant_message.content or ""
    if not reply and function_call:
        reply = "The current local time is {result}.".format(result=result)
    return ChatResponse(reply=reply)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
