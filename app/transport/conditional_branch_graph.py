"""LangGraph demo: ``add_conditional_edges`` (no checkpoint)."""

from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from typing_extensions import NotRequired, TypedDict


class BranchDemoState(TypedDict):
    input_text: str
    branch: NotRequired[str]
    output_text: NotRequired[str]


def build_conditional_branch_graph(llm: BaseChatModel):
    async def entry(_: BranchDemoState) -> dict[str, Any]:
        return {}

    def route_by_input(state: BranchDemoState) -> Literal["math", "general"]:
        text = state["input_text"].lower()
        if any(op in state["input_text"] for op in "+-*/") or "calculate" in text or "sum" in text:
            return "math"
        return "general"

    async def math_path(state: BranchDemoState) -> dict[str, str]:
        system = SystemMessage(
            content="You are a math helper. Solve or explain the calculation briefly."
        )
        msg = HumanMessage(content=state["input_text"])
        out = await llm.ainvoke([system, msg])
        return {"branch": "math", "output_text": str(out.content)}

    async def general_path(state: BranchDemoState) -> dict[str, str]:
        system = SystemMessage(content="You are a general assistant. Answer briefly.")
        msg = HumanMessage(content=state["input_text"])
        out = await llm.ainvoke([system, msg])
        return {"branch": "general", "output_text": str(out.content)}

    graph = StateGraph(BranchDemoState)
    graph.add_node("router", entry)
    graph.add_node("math", math_path)
    graph.add_node("general", general_path)
    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        route_by_input,
        {"math": "math", "general": "general"},
    )
    graph.add_edge("math", END)
    graph.add_edge("general", END)
    return graph.compile()
