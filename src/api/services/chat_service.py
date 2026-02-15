from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import string
import traceback
from pathlib import Path
from time import perf_counter
from typing import Any

import openai
import yaml

from . import conversation_service
from .config_service import get_selected_model, load_config, FOUNDRY_ENDPOINT
from .mcp_service import get_tools_for_phi4, call_tool, list_tools
from .runtime_service import ensure_manager
from .validation_service import sanitize_text

logger = logging.getLogger(__name__)

_AGENT_PATH = Path(__file__).resolve().parent.parent / "agent.yaml"

# Max tool-call iterations to prevent infinite loops
_MAX_TOOL_ROUNDS = 5


def _load_system_prompt() -> str:
    """Load the system prompt from agent.yaml."""
    try:
        with open(_AGENT_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("agent", {}).get("system_prompt", "You are a helpful assistant.")
    except Exception:
        return "You are a helpful assistant."


# Max characters for tool definitions in the system prompt.
# Phi-4-mini-instruct has ~16 K token context; keep tool JSON well under half.
_MAX_TOOLS_CHARS = 6000


def _compact_tool(t: dict) -> dict:
    """Return a minimal representation of a tool for embedding in the prompt."""
    params = t.get("parameters", {})
    required = params.get("required", [])
    props = params.get("properties", {})
    simple_params = {
        k: v.get("type", "string")
        for k, v in props.items()
    }
    return {
        "name": t.get("name", ""),
        "description": (t.get("description", "") or "")[:120],
        "parameters": simple_params,
        "required": required,
    }


def _build_system_message(tools: list[dict]) -> dict[str, Any]:
    """Build system message with tool descriptions embedded in content.

    Phi-4-mini function calling requires the model to see tool definitions
    in the prompt.  We embed them directly in the system message content
    so they survive OpenAI SDK serialization (the SDK drops unknown keys).

    Tool definitions are *compacted* (short descriptions, flat param types)
    so the prompt stays within the model's context window.  If even the
    compacted list exceeds ``_MAX_TOOLS_CHARS`` the list is truncated.
    """
    system_prompt = _load_system_prompt()
    if tools:
        compact = [_compact_tool(t) for t in tools]
        tools_json = json.dumps(compact)
        # Truncate if still too large
        if len(tools_json) > _MAX_TOOLS_CHARS:
            logger.warning("Tool definitions too large (%d chars) — truncating to fit", len(tools_json))
            while len(tools_json) > _MAX_TOOLS_CHARS and compact:
                compact.pop()
                tools_json = json.dumps(compact)
        system_prompt += (
            "\n\n## Available Tools\n\n"
            "You have the following tools available.  "
            "When you need to use a tool, respond ONLY with a JSON array "
            "in this exact format — no other text before or after:\n"
            '[{"name": "tool_name", "arguments": {"param": "value"}}]\n\n'
            "If you do NOT need a tool, respond normally with plain text.\n\n"
            f"Tools:\n```json\n{tools_json}\n```"
        )
    return {"role": "system", "content": system_prompt}


def _parse_tool_calls(response_text: str) -> list[dict] | None:
    """Parse Phi-4 function-call response into structured tool calls.

    Phi-4 returns tool calls as a JSON array:
    [{"name": "tool_name", "arguments": {...}}]
    """
    if not response_text:
        return None

    text = response_text.strip()

    # Try direct JSON parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list) and len(parsed) > 0 and "name" in parsed[0]:
            return parsed
    except json.JSONDecodeError:
        pass

    # Try to extract JSON array from response text
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list) and len(parsed) > 0 and "name" in parsed[0]:
                return parsed
        except json.JSONDecodeError:
            pass

    return None


async def _invoke_model_raw(prepared_messages: list[dict], tools: list[dict]) -> str:
    """Call the Foundry Local model and return raw response text.

    The OpenAI SDK call is blocking, so it runs in a thread to avoid
    stalling the async event loop.  Includes one automatic retry when the
    Foundry Local endpoint connection is refused (stale endpoint).
    """

    def _sync_call() -> str:
        alias = get_selected_model()
        logger.debug("_invoke_model_raw  selected_model=%r", alias)

        manager, model_id = ensure_manager(alias)
        logger.debug("Model ready  model_id=%s  endpoint=%s", model_id, FOUNDRY_ENDPOINT)

        # Use the hardcoded FOUNDRY_ENDPOINT directly — no SDK dependency
        # max_retries=0 prevents the SDK from auto-retrying huge prompts
        # which can crash the Foundry Local service
        client = openai.OpenAI(base_url=FOUNDRY_ENDPOINT, api_key="OPENAI_API_KEY", max_retries=0)
        logger.debug("OpenAI client created  base_url=%s", FOUNDRY_ENDPOINT)

        system_msg = _build_system_message(tools)
        chat_messages = [system_msg, *prepared_messages]
        max_tokens = load_config(include_secrets=True).get("maxTokens", 2048)

        logger.debug("Sending %d messages to model (max_tokens=%d)", len(chat_messages), max_tokens)
        for i, m in enumerate(chat_messages):
            role = m.get('role', '?')
            content = m.get('content', '')[:200]
            logger.debug("  msg[%d] role=%s content=%s%s", i, role, content, "..." if len(m.get('content', '')) > 200 else "")

        try:
            t0 = perf_counter()
            response = client.chat.completions.create(
                model=model_id,
                messages=chat_messages,
                max_tokens=max_tokens,
            )
            elapsed = (perf_counter() - t0) * 1000
            result = response.choices[0].message.content or ""
            logger.debug("Model responded in %.0fms  len=%d  preview=%r",
                         elapsed, len(result), result[:300])
            return result
        except openai.APIConnectionError:
            logger.warning("Connection refused — resetting manager and retrying once")
            from .runtime_service import _reset_manager
            _reset_manager()
            manager2, model_id2 = ensure_manager(alias)
            client2 = openai.OpenAI(base_url=FOUNDRY_ENDPOINT, api_key="OPENAI_API_KEY", max_retries=0)
            logger.info("Retry: endpoint=%s  model_id=%s", FOUNDRY_ENDPOINT, model_id2)
            t0 = perf_counter()
            response = client2.chat.completions.create(
                model=model_id2,
                messages=chat_messages,
                max_tokens=max_tokens,
            )
            elapsed = (perf_counter() - t0) * 1000
            result = response.choices[0].message.content or ""
            logger.info("Retry succeeded in %.0fms  len=%d", elapsed, len(result))
            return result
        except openai.InternalServerError as exc:
            logger.error("Foundry returned 500 — prompt may be too large.  "
                         "system_chars=%d  total_msgs=%d",
                         len(chat_messages[0].get('content', '')),
                         len(chat_messages))
            raise RuntimeError(
                "Model returned 500 Internal Server Error — "
                "the prompt (with tool definitions) may exceed the context window."
            ) from exc
        except Exception:
            logger.error("OpenAI completions.create() FAILED:\n%s", traceback.format_exc())
            raise

    return await asyncio.to_thread(_sync_call)


async def _run_agentic_loop(prepared_messages: list[dict[str, str]]) -> str:
    """Run the agentic tool-calling loop with Phi-4.

    Flow:
    1. Get available MCP tools
    2. Send messages + tools to model
    3. If model returns tool calls, execute them via MCP
    4. Append tool results and re-invoke model
    5. Repeat until model returns a final text response (or max rounds)
    """
    mcp_tools = get_tools_for_phi4()

    # Lazy discovery: if no tools cached but config has servers, discover now
    if not mcp_tools:
        from .mcp_service import discover_all_tools, load_mcp_config
        cfg = load_mcp_config()
        if cfg.get("mcp", {}).get("servers", {}):
            logger.info("No MCP tools cached but config has servers — discovering now")
            try:
                await discover_all_tools()
                mcp_tools = get_tools_for_phi4()
            except Exception as exc:
                logger.warning("MCP discover failed (non-fatal): %s", exc)

    working_messages = list(prepared_messages)

    for round_num in range(_MAX_TOOL_ROUNDS):
        logger.info("Agentic loop round %d (tools available: %d)", round_num + 1, len(mcp_tools))

        response_text = await _invoke_model_raw(working_messages, mcp_tools)

        # Check if the model wants to call tools
        tool_calls = _parse_tool_calls(response_text)

        if not tool_calls:
            # No tool call — this is the final response
            return response_text

        logger.info("Model requested %d tool call(s)", len(tool_calls))

        # Generate a tool call ID and append assistant message
        tool_call_id = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
        working_messages.append({
            "role": "assistant",
            "content": response_text,
        })

        # Execute each tool call and append results
        for tc in tool_calls:
            fn_name = tc.get("name", "")
            fn_args = tc.get("arguments", {})

            logger.info("Executing tool '%s' with args: %s", fn_name, fn_args)

            try:
                result = await call_tool(fn_name, fn_args)
            except Exception as exc:
                logger.error("Tool call '%s' failed: %s", fn_name, exc)
                result = json.dumps({"error": str(exc)})

            working_messages.append({
                "role": "tool",
                "content": result,
            })

    # If we exhausted rounds, return last model output
    return await _invoke_model_raw(working_messages, mcp_tools)


async def create_reply(messages: list[dict[str, Any]], conversation_id: str | None = None) -> dict:
    prepared_messages: list[dict[str, str]] = [
        {"role": item.get("role", "user"), "content": sanitize_text(item.get("content", ""))}
        for item in messages
        if item.get("content")
    ]
    if not prepared_messages:
        raise ValueError("messages must not be empty")

    chart_payload = None

    try:
        t0 = perf_counter()
        reply_text = await _run_agentic_loop(prepared_messages)
        elapsed_ms = (perf_counter() - t0) * 1000
        logger.info("Agentic loop completed in %.0fms", elapsed_ms)
        if not reply_text:
            logger.warning("Agentic loop returned empty text — using 'No content'")
            reply_text = "No content"
    except Exception as exc:
        logger.error("===== CHAT REPLY FAILED — FALLING BACK TO ECHO =====")
        logger.error("Exception type: %s", type(exc).__name__)
        logger.error("Exception message: %s", exc)
        logger.error("Full traceback:\n%s", traceback.format_exc())
        latest_user = next((m for m in reversed(prepared_messages) if m["role"] == "user"), prepared_messages[-1])
        reply_text = f"Echo: {latest_user['content']}"

    updated_messages = [*prepared_messages, {"role": "assistant", "content": reply_text}]
    stored = conversation_service.save_conversation(updated_messages, conversation_id=conversation_id)

    return {
        "reply": reply_text,
        "chart": chart_payload,
        "conversationId": stored["id"],
    }
