"""Build AgentCard protobuf objects for registered A2A agents."""

from __future__ import annotations

from a2a.types.a2a_pb2 import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import PROTOCOL_VERSION_1_0, TransportProtocol

from app.transport.a2a.registry import A2aAgentDefinition


def build_agent_card(
    definition: A2aAgentDefinition,
    public_base_url: str,
) -> AgentCard:
    base = public_base_url.rstrip("/")
    rpc_url = f"{base}{definition.path}/"

    skill = AgentSkill(
        id=definition.skill_id,
        name=definition.skill_name,
        description=definition.skill_description,
        tags=[definition.name],
        examples=list(definition.examples),
    )

    card = AgentCard(
        name=f"{definition.name.title()} Agent",
        description=definition.description,
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )
    card.supported_interfaces.add(
        url=rpc_url,
        protocol_binding=TransportProtocol.JSONRPC.value,
        protocol_version=PROTOCOL_VERSION_1_0,
    )
    return card


def agent_card_url(definition: A2aAgentDefinition) -> str:
    return f"{definition.path}/.well-known/agent-card.json"
