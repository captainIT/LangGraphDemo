from typing import Any

from pydantic import BaseModel, Field


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(min_length=1, max_length=100)
    arguments: dict[str, Any] = Field(default_factory=dict)
