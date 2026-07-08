from typing import Any

from pydantic import BaseModel, Field


class A2aAgentInfo(BaseModel):
    name: str
    description: str
    path: str
    skill_id: str
    skill_name: str
    sample_message: str
    requires_llm: bool = False
    mounted: bool = True


class A2aMessageRequest(BaseModel):
    agent_name: str = Field(min_length=1, max_length=100)
    input_text: str = Field(min_length=1, max_length=8000)


class A2aMessageResult(BaseModel):
    agent_name: str
    input_text: str
    response_chunks: list[str] = Field(default_factory=list)
    output_text: str = ""


class A2aFlowStep(BaseModel):
    step: str
    status: str
    detail: dict[str, Any] = Field(default_factory=dict)


class A2aFullFlowRequest(BaseModel):
    agent_names: list[str] | None = Field(
        default=None,
        description="Subset of A2A agents to test; defaults to all mounted agents",
    )
    use_sample_messages: bool = Field(
        default=True,
        description="When true, use each agent's built-in sample message",
    )
    input_text: str | None = Field(
        default=None,
        description="Override message text for all selected agents",
    )


class A2aFullFlowResult(BaseModel):
    agents: list[str] = Field(default_factory=list)
    messages: list[A2aMessageResult] = Field(default_factory=list)
    steps: list[A2aFlowStep] = Field(default_factory=list)
