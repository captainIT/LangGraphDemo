"""MCP stdio server exposing math tools."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("math")


@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers and return the result."""
    return a + b


@mcp.tool()
def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers and return the result."""
    return a * b


if __name__ == "__main__":
    mcp.run(transport="stdio")
