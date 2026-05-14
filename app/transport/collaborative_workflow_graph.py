import operator
from typing import Annotated, Any

from langgraph.graph import END, START, StateGraph
from typing_extensions import NotRequired, TypedDict

from app.schemas.agent import AgentType
from app.service.agent_execution import run_agent_turn
from app.service.agent_prompts import route_user_intent
from app.transport.llm_client import LlmClient


class WorkflowState(TypedDict):
    input_text: str
    steps: Annotated[list[str], operator.add]
    route_info: NotRequired[dict[str, object]]
    primary_agent: NotRequired[str]
    primary_output: NotRequired[str]
    output_text: NotRequired[str]


def build_collaborative_workflow_graph(llm: LlmClient):
    async def route_node(state: WorkflowState) -> dict[str, Any]:
        text = state["input_text"]
        route_info = await route_user_intent(llm, text)
        primary_value = str(route_info.get("primary_agent", AgentType.qa_agent.value))
        if primary_value not in {item.value for item in AgentType}:
            primary_value = AgentType.qa_agent.value
        return {
            "route_info": route_info,
            "primary_agent": primary_value,
            "steps": [f"routed_to:{primary_value}"],
        }

    async def primary_node(state: WorkflowState) -> dict[str, Any]:
        agent = AgentType(state["primary_agent"])
        out = await run_agent_turn(llm, agent, state["input_text"])
        return {
            "primary_output": out,
            "output_text": out,
            "steps": [f"executed:{agent.value}"],
        }

    async def maybe_summarize_node(state: WorkflowState) -> dict[str, Any]:
        route_info = state.get("route_info") or {}
        primary_agent = AgentType(state["primary_agent"])
        current = state.get("output_text", "")
        if bool(route_info.get("should_summarize", False)) and primary_agent != AgentType.summary_agent:
            summarized = await run_agent_turn(llm, AgentType.summary_agent, current)
            return {"output_text": summarized, "steps": ["executed:summary_agent"]}
        return {}

    async def maybe_translate_node(state: WorkflowState) -> dict[str, Any]:
        route_info = state.get("route_info") or {}
        primary_agent = AgentType(state["primary_agent"])
        current = state.get("output_text", "")
        if bool(route_info.get("should_translate", False)) and primary_agent != AgentType.translate_agent:
            translated = await run_agent_turn(llm, AgentType.translate_agent, current)
            return {"output_text": translated, "steps": ["executed:translate_agent"]}
        return {}

    graph = StateGraph(WorkflowState)
    graph.add_node("route", route_node)
    graph.add_node("primary", primary_node)
    graph.add_node("maybe_summarize", maybe_summarize_node)
    graph.add_node("maybe_translate", maybe_translate_node)
    graph.add_edge(START, "route")
    graph.add_edge("route", "primary")
    graph.add_edge("primary", "maybe_summarize")
    graph.add_edge("maybe_summarize", "maybe_translate")
    graph.add_edge("maybe_translate", END)
    return graph.compile()
