"""MCP stdio server exposing time tools."""

from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("time")


@mcp.tool()
def get_current_utc_time() -> str:
    """Get current UTC time in ISO8601 format."""
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    mcp.run(transport="stdio")
