from collections.abc import AsyncIterator
from typing import Any

from app.schemas.agent import AgentType
from app.service.agent_execution import TOOL_AGENT_SYSTEM_PROMPT, run_agent_turn
from app.service.agent_prompts import build_system_prompt
from app.transport.collaborative_workflow_graph import build_collaborative_workflow_graph
from app.transport.llm_client import LlmClient
from app.utils.tool_functions import (
    add_numbers,
    count_words,
    get_current_utc_time,
    slugify_text,
)


class AgentService:
    def __init__(self, llm_client: LlmClient) -> None:
        self._llm_client = llm_client
        self._collaborative_graph = build_collaborative_workflow_graph(llm_client)

    async def run_agent(self, agent_type: AgentType, input_text: str) -> str:
        return await run_agent_turn(self._llm_client, agent_type, input_text)

    async def run_tool_agent_with_trace(
        self, input_text: str
    ) -> tuple[str, list[dict[str, Any]]]:
        return await self._llm_client.ask_with_tools_and_trace(
            system_prompt=TOOL_AGENT_SYSTEM_PROMPT,
            user_input=input_text,
            tools=[get_current_utc_time, add_numbers, count_words, slugify_text],
        )

    async def run_collaborative_workflow(self, input_text: str) -> tuple[list[str], str]:
        result = await self._collaborative_graph.ainvoke(
            {"input_text": input_text, "steps": []},
        )
        steps = result.get("steps") or []
        output_text = str(result.get("output_text", ""))
        return steps, output_text

    async def stream_agent(self, agent_type: AgentType, input_text: str) -> AsyncIterator[str]:
        prompt = build_system_prompt(agent_type)
        async for chunk in self._llm_client.stream_ask(prompt, input_text):
            yield chunk

    def list_agents(self) -> list[str]:
        return [item.value for item in AgentType]
