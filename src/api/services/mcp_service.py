"""MCP (Model Context Protocol) service for managing tool servers.

Uses the official ``mcp`` Python SDK to spawn MCP servers as stdio child
processes, discover their tools, and route tool invocations from the
Phi-4 agentic loop.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from .path_service import STORAGE_DIR, ensure_storage_dirs

logger = logging.getLogger(__name__)

MCP_CONFIG_PATH = STORAGE_DIR / "mcp.json"

# In-memory registry of discovered tools
_tools: list[dict[str, Any]] = []

# Map tool name -> server name for routing invocations
_tool_server_map: dict[str, str] = {}

# Map server name -> server config for invocations
_server_configs: dict[str, dict[str, Any]] = {}

# Timeout for MCP server operations (seconds)
_MCP_TIMEOUT = 30


def _default_mcp_config() -> dict:
    return {"mcp": {"servers": {}}}


def load_mcp_config() -> dict:
    """Load MCP config from mcp.json."""
    ensure_storage_dirs()
    if not MCP_CONFIG_PATH.exists():
        save_mcp_config(_default_mcp_config())
    return json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))


def save_mcp_config(config: dict) -> dict:
    """Save MCP config to mcp.json."""
    ensure_storage_dirs()
    MCP_CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config


async def _discover_tools_from_server(
    server_name: str, server_cfg: dict
) -> list[dict[str, Any]]:
    """Spawn an MCP server via the SDK and list its tools."""
    command = server_cfg.get("command", "")
    args = server_cfg.get("args", [])
    env_vars = server_cfg.get("env", {})

    if not command:
        logger.warning("MCP server '%s' has no command, skipping", server_name)
        return []

    proc_env = {**os.environ, **env_vars}
    params = StdioServerParameters(command=command, args=args, env=proc_env)

    logger.info("Discovering tools from MCP server '%s': %s %s", server_name, command, args)

    tools: list[dict[str, Any]] = []
    try:
        async with asyncio.timeout(_MCP_TIMEOUT):
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    for t in result.tools:
                        tools.append(
                            {
                                "name": t.name,
                                "description": t.description or "",
                                "parameters": t.inputSchema
                                if hasattr(t, "inputSchema")
                                else {},
                                "serverName": server_name,
                            }
                        )
        logger.info(
            "Discovered %d tools from MCP server '%s'", len(tools), server_name
        )
    except TimeoutError:
        logger.error(
            "Tool discovery timed out for MCP server '%s' (%ds)", server_name, _MCP_TIMEOUT
        )
    except Exception as exc:
        logger.error("Tool discovery failed for MCP server '%s': %s", server_name, exc)

    return tools


async def discover_all_tools() -> list[dict[str, Any]]:
    """Discover tools from all configured MCP servers."""
    global _tools, _tool_server_map, _server_configs

    config = load_mcp_config()
    servers = config.get("mcp", {}).get("servers", {})

    _tools = []
    _tool_server_map = {}
    _server_configs = {}

    for server_name, server_cfg in servers.items():
        _server_configs[server_name] = server_cfg
        discovered = await _discover_tools_from_server(server_name, server_cfg)
        for tool in discovered:
            _tools.append(tool)
            _tool_server_map[tool["name"]] = server_name

    logger.info("Total MCP tools discovered: %d", len(_tools))
    return _tools


def list_tools() -> list[dict[str, Any]]:
    """Return currently registered MCP tools."""
    return list(_tools)


def get_tools_for_phi4() -> list[dict[str, Any]]:
    """Format discovered tools for Phi-4 function-calling system prompt.

    Returns tool definitions in the format Phi-4-mini expects:
    [{"name": "...", "description": "...", "parameters": {...}}]

    Keeps the original JSON Schema parameter structure so the model
    can see property names, types, descriptions, and required fields.
    """
    phi4_tools = []
    for tool in _tools:
        params = tool.get("parameters", {})
        phi4_tools.append(
            {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": params,
            }
        )
    return phi4_tools


async def call_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """Invoke a tool on its MCP server and return the result as a string.

    Spawns the server via the SDK, sends initialize + tools/call, returns
    result content.
    """
    server_name = _tool_server_map.get(tool_name)
    if not server_name:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    server_cfg = _server_configs.get(server_name)
    if not server_cfg:
        return json.dumps({"error": f"No config for server: {server_name}"})

    command = server_cfg.get("command", "")
    args = server_cfg.get("args", [])
    env_vars = server_cfg.get("env", {})
    proc_env = {**os.environ, **env_vars}

    params = StdioServerParameters(command=command, args=args, env=proc_env)

    logger.info(
        "Calling tool '%s' on MCP server '%s' with args: %s",
        tool_name,
        server_name,
        arguments,
    )

    try:
        async with asyncio.timeout(_MCP_TIMEOUT):
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    texts: list[str] = []
                    for item in result.content:
                        if hasattr(item, "text"):
                            texts.append(item.text)
                        else:
                            texts.append(json.dumps(item.model_dump()))
                    return "\n".join(texts) if texts else json.dumps({"result": "empty"})
    except TimeoutError:
        logger.error("Tool call '%s' timed out (%ds)", tool_name, _MCP_TIMEOUT)
        return json.dumps({"error": f"Tool call timed out after {_MCP_TIMEOUT}s"})
    except Exception as exc:
        logger.error("Tool call '%s' failed: %s", tool_name, exc)
        return json.dumps({"error": str(exc)})
