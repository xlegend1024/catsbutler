from __future__ import annotations

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from pathlib import Path

import yaml

# ── Logging ───────────────────────────────────────────────────────
# Set LOG_LEVEL=DEBUG for verbose dev diagnostics; defaults to INFO
import os as _os
_LOG_LEVEL = getattr(logging, _os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(
    level=_LOG_LEVEL,
    format="%(asctime)s  %(levelname)-7s  [%(name)s]  %(message)s",
    datefmt="%H:%M:%S",
)
# Quiet noisy third-party loggers
for _noisy in ("httpcore", "httpx", "urllib3", "asyncio", "watchfiles", "multipart"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Ensure src/api is on sys.path so `python src/api/foundry_api.py` works from any cwd
_API_DIR = str(Path(__file__).resolve().parent)
if _API_DIR not in sys.path:
    sys.path.insert(0, _API_DIR)

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from schemas.chat import ChatRequest, ChatResponse
from schemas.conversation import ConversationRecord, ConversationSummary
from schemas.mcp import McpConfig, McpTool, McpToolList
from schemas.runtime import ModelListResponse, ServiceState
from schemas.stock import AppConfigurationUpdate, StockQueryResult
from services import chat_service, config_service, conversation_service, mcp_service, model_service, runtime_service, stock_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Startup / shutdown lifecycle for the application."""
    # ── startup ──
    logger.info("Expecting Foundry Local service on port %d", config_service.FOUNDRY_PORT)
    logger.info("If not running, start it with:  foundry service start --port %d", config_service.FOUNDRY_PORT)
    try:
        model_service.list_models()
    except Exception as exc:
        logger.warning("Model listing failed at startup (non-fatal): %s", exc)
    try:
        await mcp_service.discover_all_tools()
    except Exception:
        pass  # non-fatal; user can reload manually
    yield
    # ── shutdown (nothing to clean up yet) ──


app = FastAPI(title="CatsButler Local Chat API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self' http://localhost:8000 http://127.0.0.1:8000"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(ValueError)
async def value_error_handler(_, exc: ValueError):
    return JSONResponse(status_code=400, content={"error": "validation_error", "detail": str(exc)})


@app.get("/agent")
def get_agent() -> dict:
    agent_path = Path(__file__).resolve().parent / "agent.yaml"
    with open(agent_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("agent", {})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/service/status", response_model=ServiceState)
def get_service_status() -> ServiceState:
    return ServiceState.model_validate(runtime_service.status())


@app.post("/service/start", response_model=ServiceState)
def start_service() -> ServiceState:
    selected = config_service.get_selected_model()
    state = runtime_service.start(selected)
    return ServiceState.model_validate(state)


@app.post("/service/stop", response_model=ServiceState)
def stop_service() -> ServiceState:
    state = runtime_service.stop()
    return ServiceState.model_validate(state)


@app.get("/models", response_model=ModelListResponse)
def list_models() -> ModelListResponse:
    return ModelListResponse(items=model_service.list_models())


@app.get("/config")
def get_config() -> dict:
    return config_service.load_config(include_secrets=False)


@app.put("/config")
def put_config(payload: AppConfigurationUpdate) -> dict:
    return config_service.save_config(payload.model_dump())


@app.post("/chat", response_model=ChatResponse)
async def post_chat(payload: ChatRequest) -> ChatResponse:
    response = await chat_service.create_reply(
        [message.model_dump() for message in payload.messages],
        conversation_id=payload.conversationId,
    )
    return ChatResponse.model_validate(response)


@app.get("/stocks/quote", response_model=StockQueryResult)
def get_stock_quote(symbol: str = Query(..., min_length=1, max_length=8)) -> StockQueryResult:
    return StockQueryResult.model_validate(stock_service.get_quote(symbol))


@app.get("/conversations")
def get_conversations() -> dict[str, list[ConversationSummary]]:
    items = [ConversationSummary.model_validate(item) for item in conversation_service.list_conversations()]
    return {"items": items}


@app.get("/conversations/{conversation_id}", response_model=ConversationRecord)
def get_conversation(conversation_id: str) -> ConversationRecord:
    try:
        payload = conversation_service.get_conversation(conversation_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="conversation not found") from exc
    return ConversationRecord.model_validate(payload)


# ── MCP endpoints ──────────────────────────────────────────────────

@app.get("/mcp/config")
def get_mcp_config() -> dict:
    return mcp_service.load_mcp_config()


@app.put("/mcp/config")
async def put_mcp_config(payload: McpConfig) -> dict:
    saved = mcp_service.save_mcp_config(payload.model_dump())
    # Auto-discover tools after config change so they're available immediately
    try:
        await mcp_service.discover_all_tools()
    except Exception:
        pass  # non-fatal; user can retry with Reload Tools
    return saved


@app.get("/mcp/tools", response_model=McpToolList)
def list_mcp_tools() -> McpToolList:
    tools = mcp_service.list_tools()
    return McpToolList(items=[McpTool.model_validate(t) for t in tools])


@app.post("/mcp/reload", response_model=McpToolList)
async def reload_mcp_servers() -> McpToolList:
    tools = await mcp_service.discover_all_tools()
    return McpToolList(items=[McpTool.model_validate(t) for t in tools])





if __name__ == "__main__":
    import uvicorn

    logger.info("Starting %s", app.title)

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level=_os.environ.get("LOG_LEVEL", "info").lower())
