"""MCP stdio server exposing text processing tools."""

import re

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("text")


@mcp.tool()
def count_words(text: str) -> int:
    """Count words in a text."""
    return len(text.split())


@mcp.tool()
def slugify_text(text: str) -> str:
    """Convert text into a URL-friendly slug."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return normalized.strip("-")


if __name__ == "__main__":
    mcp.run(transport="stdio")
