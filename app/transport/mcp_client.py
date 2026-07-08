"""MCP client transport wrapping langchain-mcp-adapters."""

from __future__ import annotations

from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from app.transport.mcp.registry import build_stdio_connections


class McpClientTransport:
    def __init__(
        self,
        *,
        server_names: list[str] | None = None,
        tool_name_prefix: bool = True,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._server_names = server_names
        self._tool_name_prefix = tool_name_prefix
        self._timeout_seconds = timeout_seconds

    def create_client(self, server_names: list[str] | None = None) -> MultiServerMCPClient:
        names = server_names or self._server_names
        connections = build_stdio_connections(names)
        return MultiServerMCPClient(
            connections,
            tool_name_prefix=self._tool_name_prefix,
        )

    @property
    def timeout_seconds(self) -> float:
        return self._timeout_seconds

    def connection_summary(self, server_names: list[str] | None = None) -> list[dict[str, Any]]:
        names = server_names or list(build_stdio_connections().keys())
        connections = build_stdio_connections(names)
        return [
            {
                "server_name": name,
                "transport": config["transport"],
                "command": config["command"],
                "args": config["args"],
            }
            for name, config in connections.items()
        ]
