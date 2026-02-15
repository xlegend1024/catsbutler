from __future__ import annotations

from pydantic import BaseModel, Field


class McpServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    type: str = Field(default="stdio", description="Transport type (only 'stdio' supported)")
    command: str = Field(min_length=1, description="Executable to run (e.g. 'uvx', 'npx')")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")


class McpServers(BaseModel):
    """Map of server name -> server config."""

    servers: dict[str, McpServerConfig] = Field(default_factory=dict)


class McpConfig(BaseModel):
    """Root MCP configuration matching mcp.json structure."""

    mcp: McpServers = Field(default_factory=McpServers)


class McpTool(BaseModel):
    """A discovered tool from an MCP server."""

    name: str
    description: str = ""
    parameters: dict = Field(default_factory=dict)
    serverName: str = ""


class McpToolList(BaseModel):
    """Response wrapper for tool listing."""

    items: list[McpTool] = Field(default_factory=list)
