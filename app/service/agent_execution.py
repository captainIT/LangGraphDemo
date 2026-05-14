from app.schemas.agent import AgentType
from app.service.agent_prompts import build_system_prompt
from app.transport.llm_client import LlmClient
from app.utils.tool_functions import (
    add_numbers,
    count_words,
    get_current_utc_time,
    slugify_text,
)

TOOL_AGENT_SYSTEM_PROMPT = (
    "You can call tools for utility tasks. "
    "Available tools are get_current_utc_time, add_numbers, count_words, slugify_text. "
    "Prefer tools when user asks about those tasks."
)

_TOOL_BINDINGS = [get_current_utc_time, add_numbers, count_words, slugify_text]


async def run_agent_turn(llm: LlmClient, agent_type: AgentType, input_text: str) -> str:
    if agent_type == AgentType.tool_agent:
        return await llm.ask_with_tools(
            system_prompt=TOOL_AGENT_SYSTEM_PROMPT,
            user_input=input_text,
            tools=list(_TOOL_BINDINGS),
        )
    prompt = build_system_prompt(agent_type)
    return await llm.ask(system_prompt=prompt, user_input=input_text)
