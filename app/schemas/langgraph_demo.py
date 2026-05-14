from pydantic import BaseModel, Field


class LangGraphCheckpointDemoRequest(BaseModel):
    """Continue a checkpointed thread by ``thread_id`` (in-memory demo saver)."""

    thread_id: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")
    input_text: str = Field(min_length=1, max_length=6000)


class LangGraphCheckpointDemoResult(BaseModel):
    thread_id: str
    message_count: int
    assistant_reply: str


class LangGraphConditionalDemoRequest(BaseModel):
    input_text: str = Field(min_length=1, max_length=6000)


class LangGraphConditionalDemoResult(BaseModel):
    branch: str
    output_text: str


class LangGraphReactDemoRequest(BaseModel):
    input_text: str = Field(min_length=1, max_length=6000)


class LangGraphReactDemoResult(BaseModel):
    output_text: str
    tool_turns: int = Field(description="Approximate tool round-trips (ToolMessage count).")
