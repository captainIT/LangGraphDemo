import re
from datetime import datetime, timezone

from langchain_core.tools import tool


@tool
def get_current_utc_time() -> str:
    """Get current UTC time in ISO8601 format."""
    return datetime.now(timezone.utc).isoformat()


@tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers and return the result."""
    return a + b


@tool
def count_words(text: str) -> int:
    """Count words in a text."""
    return len(text.split())


@tool
def slugify_text(text: str) -> str:
    """Convert text into a URL-friendly slug."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return normalized.strip("-")
