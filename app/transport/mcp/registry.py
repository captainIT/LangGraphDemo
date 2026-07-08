"""MCP server registry and stdio connection configuration."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SERVERS_DIR = Path(__file__).resolve().parent / "servers"


@dataclass(frozen=True)
class McpServerDefinition:
    name: str
    description: str
    script_path: Path
    tool_names: tuple[str, ...]


MCP_SERVER_DEFINITIONS: tuple[McpServerDefinition, ...] = (
    McpServerDefinition(
        name="math",
        description="Arithmetic tools exposed via MCP stdio",
        script_path=_SERVERS_DIR / "math_server.py",
        tool_names=("add_numbers", "multiply_numbers"),
    ),
    McpServerDefinition(
        name="time",
        description="UTC time tools exposed via MCP stdio",
        script_path=_SERVERS_DIR / "time_server.py",
        tool_names=("get_current_utc_time",),
    ),
    McpServerDefinition(
        name="text",
        description="Text processing tools exposed via MCP stdio",
        script_path=_SERVERS_DIR / "text_server.py",
        tool_names=("count_words", "slugify_text"),
    ),
)

MCP_SERVER_MAP: dict[str, McpServerDefinition] = {
    definition.name: definition for definition in MCP_SERVER_DEFINITIONS
}


def build_stdio_connections(
    server_names: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build MultiServerMCPClient stdio connection configs."""
    selected = server_names or list(MCP_SERVER_MAP.keys())
    connections: dict[str, dict[str, Any]] = {}
    for name in selected:
        definition = MCP_SERVER_MAP.get(name)
        if definition is None:
            raise ValueError(f"Unsupported MCP server: {name}")
        if not definition.script_path.is_file():
            raise FileNotFoundError(f"MCP server script not found: {definition.script_path}")
        connections[name] = {
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(definition.script_path)],
        }
    return connections
