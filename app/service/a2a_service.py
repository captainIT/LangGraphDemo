"""A2A orchestration: agent discovery, messaging, and full-flow smoke tests."""

from __future__ import annotations

import logging

from app.config import Settings
from app.schemas.a2a import (
    A2aAgentInfo,
    A2aFlowStep,
    A2aFullFlowResult,
    A2aMessageResult,
)
from app.transport.a2a.registry import A2A_AGENT_DEFINITIONS, A2A_AGENT_MAP
from app.transport.a2a_client import A2aClientTransport

logger = logging.getLogger(__name__)


class A2aService:
    def __init__(self, transport: A2aClientTransport, settings: Settings) -> None:
        self._transport = transport
        self._settings = settings

    def list_agents(self) -> list[A2aAgentInfo]:
        llm_available = bool(self._settings.openai_api_key)
        return [
            A2aAgentInfo(
                name=definition.name,
                description=definition.description,
                path=definition.path,
                skill_id=definition.skill_id,
                skill_name=definition.skill_name,
                sample_message=definition.sample_message,
                requires_llm=definition.requires_llm,
                mounted=(not definition.requires_llm) or llm_available,
            )
            for definition in A2A_AGENT_DEFINITIONS
        ]

    async def get_agent_card(self, agent_name: str) -> dict:
        definition = self._resolve_agent(agent_name)
        if definition.requires_llm and not self._settings.openai_api_key:
            raise ValueError(
                f"A2A agent '{agent_name}' requires OPENAI_API_KEY to be mounted"
            )
        return await self._transport.fetch_agent_card_dict(definition.path)

    async def send_message(
        self,
        agent_name: str,
        input_text: str,
    ) -> A2aMessageResult:
        definition = self._resolve_agent(agent_name)
        if definition.requires_llm and not self._settings.openai_api_key:
            raise ValueError(
                f"A2A agent '{agent_name}' requires OPENAI_API_KEY to be mounted"
            )

        chunks, _card = await self._transport.send_text_message(
            definition.path,
            input_text,
        )
        return A2aMessageResult(
            agent_name=agent_name,
            input_text=input_text,
            response_chunks=chunks,
            output_text=chunks[-1] if chunks else "",
        )

    async def run_full_flow(
        self,
        agent_names: list[str] | None = None,
        use_sample_messages: bool = True,
        input_text: str | None = None,
    ) -> A2aFullFlowResult:
        selected = agent_names or [item.name for item in self.list_agents() if item.mounted]
        steps: list[A2aFlowStep] = []
        messages: list[A2aMessageResult] = []

        steps.append(
            A2aFlowStep(
                step="resolve_agents",
                status="ok",
                detail={"agents": selected},
            )
        )

        for agent_name in selected:
            definition = self._resolve_agent(agent_name)
            if definition.requires_llm and not self._settings.openai_api_key:
                steps.append(
                    A2aFlowStep(
                        step="fetch_agent_card",
                        status="error",
                        detail={
                            "agent_name": agent_name,
                            "error": "OPENAI_API_KEY is not configured",
                        },
                    )
                )
                continue

            try:
                card_dict = await self._transport.fetch_agent_card_dict(definition.path)
                steps.append(
                    A2aFlowStep(
                        step="fetch_agent_card",
                        status="ok",
                        detail={
                            "agent_name": agent_name,
                            "card": card_dict,
                        },
                    )
                )
            except Exception as exc:
                logger.exception(
                    "a2a agent card fetch failed",
                    extra={"agent_name": agent_name},
                )
                steps.append(
                    A2aFlowStep(
                        step="fetch_agent_card",
                        status="error",
                        detail={"agent_name": agent_name, "error": str(exc)},
                    )
                )
                continue

            message_text = input_text
            if not message_text:
                message_text = definition.sample_message if use_sample_messages else "hello a2a"

            try:
                result = await self.send_message(agent_name, message_text)
                messages.append(result)
                steps.append(
                    A2aFlowStep(
                        step="send_message",
                        status="ok",
                        detail={
                            "agent_name": agent_name,
                            "input_text": message_text,
                            "output_text": result.output_text,
                        },
                    )
                )
            except Exception as exc:
                logger.exception(
                    "a2a message send failed",
                    extra={"agent_name": agent_name},
                )
                steps.append(
                    A2aFlowStep(
                        step="send_message",
                        status="error",
                        detail={
                            "agent_name": agent_name,
                            "input_text": message_text,
                            "error": str(exc),
                        },
                    )
                )

        steps.append(A2aFlowStep(step="complete", status="ok", detail={}))
        return A2aFullFlowResult(agents=selected, messages=messages, steps=steps)

    @staticmethod
    def _resolve_agent(agent_name: str):
        if agent_name not in A2A_AGENT_MAP:
            raise ValueError(f"Unsupported A2A agent: {agent_name}")
        return A2A_AGENT_MAP[agent_name]
