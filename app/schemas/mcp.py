from typing import Any

from pydantic import BaseModel, Field


class McpServerInfo(BaseModel):
    name: str
    description: str
    transport: str = "stdio"
    tool_names: list[str] = Field(default_factory=list)


class McpToolInfo(BaseModel):
    name: str
    description: str = ""
    server_name: str | None = None
    input_schema: dict[str, Any] = Field(default_factory=dict)


class McpToolInvokeRequest(BaseModel):
    tool_name: str = Field(min_length=1, max_length=200)
    arguments: dict[str, Any] = Field(default_factory=dict)
    server_name: str | None = Field(
        default=None,
        description="Optional MCP server filter when resolving prefixed tool names",
    )


class McpToolInvokeResult(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any = None


class McpFlowStep(BaseModel):
    step: str
    status: str
    detail: dict[str, Any] = Field(default_factory=dict)


class McpFullFlowRequest(BaseModel):
    server_names: list[str] | None = Field(
        default=None,
        description="Subset of MCP servers to test; defaults to all configured servers",
    )
    include_tool_invocations: bool = Field(
        default=True,
        description="When true, invoke a sample tool on each server",
    )


class McpServerFlowRequest(BaseModel):
    include_tool_invocations: bool = Field(
        default=True,
        description="When true, invoke all sample tools for the target server",
    )


class McpFullFlowResult(BaseModel):
    servers: list[str] = Field(default_factory=list)
    tools: list[McpToolInfo] = Field(default_factory=list)
    invocations: list[McpToolInvokeResult] = Field(default_factory=list)
    steps: list[McpFlowStep] = Field(default_factory=list)
