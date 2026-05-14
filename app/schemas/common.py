from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = True
    message: str = "ok"
    data: dict[str, Any] = Field(default_factory=dict)
