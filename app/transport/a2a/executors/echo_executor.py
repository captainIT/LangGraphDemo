"""Simple echo AgentExecutor for A2A protocol demos."""

from __future__ import annotations

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue_v2 import EventQueue

from app.transport.a2a.task_helpers import cancel_text_task, complete_text_task


class EchoAgentExecutor(AgentExecutor):
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_input = context.get_user_input()
        response_text = f"Echo: {user_input}"
        await complete_text_task(context, event_queue, response_text)

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        await cancel_text_task(context, event_queue)
