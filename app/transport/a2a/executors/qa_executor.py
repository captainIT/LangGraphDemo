"""LLM-backed Q&A AgentExecutor for A2A protocol demos."""

from __future__ import annotations

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue_v2 import EventQueue

from app.service.agent_prompts import build_system_prompt
from app.schemas.agent import AgentType
from app.transport.a2a.task_helpers import cancel_text_task, complete_text_task
from app.transport.llm_client import LlmClient


class QaAgentExecutor(AgentExecutor):
    def __init__(self, llm_client: LlmClient) -> None:
        self._llm_client = llm_client
        self._system_prompt = build_system_prompt(AgentType.qa_agent)

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_input = context.get_user_input()
        response_text = await self._llm_client.ask(self._system_prompt, user_input)
        await complete_text_task(context, event_queue, response_text, artifact_name="answer")

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        await cancel_text_task(context, event_queue)
