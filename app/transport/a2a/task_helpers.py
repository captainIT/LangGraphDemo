"""Shared helpers for A2A AgentExecutor task lifecycle."""

from __future__ import annotations

from a2a.helpers.proto_helpers import new_task_from_user_message, new_text_part
from a2a.server.agent_execution import RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.server.tasks.task_updater import TaskUpdater


async def complete_text_task(
    context: RequestContext,
    event_queue: EventQueue,
    response_text: str,
    artifact_name: str = "result",
) -> None:
    """Run the standard task workflow: submit → work → artifact → complete."""
    message = context.message
    if message is None:
        return

    task = new_task_from_user_message(message)
    await event_queue.enqueue_event(task)

    updater = TaskUpdater(event_queue, task.id, task.context_id)
    await updater.start_work()

    part = new_text_part(response_text)
    await updater.add_artifact([part], name=artifact_name)
    await updater.complete(message=updater.new_agent_message([part]))


async def cancel_text_task(
    context: RequestContext,
    event_queue: EventQueue,
) -> None:
    task_id = context.task_id
    context_id = context.context_id
    if not task_id or not context_id:
        return

    updater = TaskUpdater(event_queue, task_id, context_id)
    await updater.cancel()
