"""Mount A2A protocol routes on the FastAPI application."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore

from app.config import Settings
from app.transport.a2a.card_builder import agent_card_url, build_agent_card
from app.transport.a2a.executors.echo_executor import EchoAgentExecutor
from app.transport.a2a.executors.qa_executor import QaAgentExecutor
from app.transport.a2a.registry import A2A_AGENT_DEFINITIONS, A2aAgentDefinition
from app.transport.llm_client import LlmClient

logger = logging.getLogger(__name__)


def _build_executor(
    definition: A2aAgentDefinition,
    llm_client: LlmClient | None,
) -> AgentExecutor:
    if definition.name == "echo":
        return EchoAgentExecutor()
    if definition.name == "qa":
        if llm_client is None:
            raise RuntimeError("LLM client is required for the A2A QA agent")
        return QaAgentExecutor(llm_client)
    raise ValueError(f"Unsupported A2A agent: {definition.name}")


def register_a2a_agents(app: FastAPI, settings: Settings) -> None:
    """Expose built-in demo agents as A2A JSON-RPC endpoints on the FastAPI app."""
    llm_client: LlmClient | None = None
    if settings.openai_api_key:
        llm_client = LlmClient(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

    mounted: list[str] = []
    for definition in A2A_AGENT_DEFINITIONS:
        if definition.requires_llm and llm_client is None:
            logger.warning(
                "Skipping A2A agent because OPENAI_API_KEY is not configured",
                extra={"agent_name": definition.name},
            )
            continue

        agent_card = build_agent_card(definition, settings.a2a_public_base_url)
        request_handler = DefaultRequestHandler(
            agent_executor=_build_executor(definition, llm_client),
            task_store=InMemoryTaskStore(),
            agent_card=agent_card,
        )

        add_a2a_routes_to_fastapi(
            app,
            agent_card_routes=create_agent_card_routes(
                agent_card,
                card_url=agent_card_url(definition),
            ),
            jsonrpc_routes=create_jsonrpc_routes(
                request_handler,
                rpc_url=f"{definition.path}/",
            ),
        )
        mounted.append(definition.name)

    logger.info("Mounted A2A demo agents", extra={"agents": mounted})
