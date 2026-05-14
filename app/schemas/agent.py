from enum import Enum

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    qa_agent = "qa_agent"
    summary_agent = "summary_agent"
    translate_agent = "translate_agent"
    planner_agent = "planner_agent"
    tool_agent = "tool_agent"


class AgentRunRequest(BaseModel):
    agent_type: AgentType
    input_text: str = Field(min_length=1, max_length=6000)


class AgentRunResult(BaseModel):
    agent_type: AgentType
    output_text: str


class ToolCallTrace(BaseModel):
    tool_name: str
    arguments: dict
    result: str


class AgentRunWithTraceResult(BaseModel):
    agent_type: AgentType
    output_text: str
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)


class AgentWorkflowRequest(BaseModel):
    input_text: str = Field(min_length=1, max_length=6000)


class AgentWorkflowResult(BaseModel):
    steps: list[str]
    output_text: str
