import json
from typing import Any

from app.schemas.agent import AgentType
from app.transport.llm_client import LlmClient

ROUTING_SYSTEM_PROMPT = (
    "You are an intent router for multiple assistants. "
    "Return strict JSON only with fields: "
    "primary_agent (qa_agent|summary_agent|translate_agent|planner_agent|tool_agent), "
    "should_summarize (boolean), should_translate (boolean). "
    "Set should_translate true when the user asks for English output. "
    "Set should_summarize true for long content requests."
)

SYSTEM_PROMPTS: dict[AgentType, str] = {
    AgentType.qa_agent: (
        "You are a concise Q&A assistant. "
        "Answer clearly and do not make up facts when uncertain."
    ),
    AgentType.summary_agent: (
        "You are a text summarization assistant. "
        "Return a concise summary with key bullet points."
    ),
    AgentType.translate_agent: (
        "You are a translation assistant. "
        "Translate user input from Chinese to English with natural tone."
    ),
    AgentType.planner_agent: (
        "You are a planning assistant. "
        "Break user goal into actionable numbered steps."
    ),
    AgentType.tool_agent: (
        "You are a tool-using assistant. "
        "Use available function calls when user asks for calculations, time lookup, "
        "word counting, or slug generation. "
        "If tools are not needed, answer normally."
    ),
}


def build_system_prompt(agent_type: AgentType) -> str:
    return SYSTEM_PROMPTS[agent_type]


def default_route_intent() -> dict[str, object]:
    return {
        "primary_agent": AgentType.qa_agent.value,
        "should_summarize": False,
        "should_translate": False,
    }


async def route_user_intent(llm: LlmClient, input_text: str) -> dict[str, object]:
    raw_output = await llm.ask(
        system_prompt=ROUTING_SYSTEM_PROMPT,
        user_input=input_text,
    )
    try:
        parsed: Any = json.loads(raw_output)
        if not isinstance(parsed, dict):
            return default_route_intent()
        return parsed
    except json.JSONDecodeError:
        return default_route_intent()
