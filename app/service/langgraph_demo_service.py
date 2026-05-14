from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from app.transport.checkpoint_chat_graph import build_checkpoint_chat_graph
from app.transport.checkpoint_store import get_demo_in_memory_saver
from app.transport.conditional_branch_graph import build_conditional_branch_graph
from app.transport.llm_client import LlmClient
from app.transport.react_prebuilt_graph import build_react_demo_graph
from app.utils.tool_functions import (
    add_numbers,
    count_words,
    get_current_utc_time,
    slugify_text,
)


class LangGraphDemoService:
    """Feature demos: checkpointed chat, conditional routing, prebuilt ReAct."""

    def __init__(self, llm_client: LlmClient) -> None:
        model = llm_client.chat_model
        saver = get_demo_in_memory_saver()
        self._checkpoint_graph = build_checkpoint_chat_graph(model, saver)
        self._branch_graph = build_conditional_branch_graph(model)
        tools = [get_current_utc_time, add_numbers, count_words, slugify_text]
        self._react_graph = build_react_demo_graph(model, tools)

    async def run_checkpoint_turn(self, thread_id: str, input_text: str) -> dict[str, object]:
        config = {"configurable": {"thread_id": thread_id}}
        result = await self._checkpoint_graph.ainvoke(
            {"messages": [HumanMessage(content=input_text)]},
            config,
        )
        messages: list[BaseMessage] = list(result.get("messages") or [])
        last = messages[-1] if messages else None
        reply = ""
        if last is not None:
            reply = str(getattr(last, "content", "") or "")
        return {
            "thread_id": thread_id,
            "message_count": len(messages),
            "assistant_reply": reply,
        }

    async def run_conditional_branch(self, input_text: str) -> dict[str, str]:
        result = await self._branch_graph.ainvoke({"input_text": input_text})
        return {
            "branch": str(result.get("branch", "")),
            "output_text": str(result.get("output_text", "")),
        }

    async def run_react_agent(self, input_text: str) -> dict[str, object]:
        result = await self._react_graph.ainvoke({"messages": [HumanMessage(content=input_text)]})
        messages: list[BaseMessage] = list(result.get("messages") or [])
        tool_turns = sum(1 for m in messages if isinstance(m, ToolMessage))
        output_text = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                tool_calls = getattr(msg, "tool_calls", None) or []
                if not tool_calls:
                    output_text = str(getattr(msg, "content", "") or "")
                    break
        if not output_text and messages:
            output_text = str(getattr(messages[-1], "content", "") or "")
        return {"output_text": output_text, "tool_turns": tool_turns}
