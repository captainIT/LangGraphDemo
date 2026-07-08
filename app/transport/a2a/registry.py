"""Registry of built-in A2A demo agents exposed by this application."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class A2aAgentDefinition:
    name: str
    description: str
    path: str
    skill_id: str
    skill_name: str
    skill_description: str
    examples: tuple[str, ...]
    sample_message: str
    requires_llm: bool = False


A2A_AGENT_DEFINITIONS: tuple[A2aAgentDefinition, ...] = (
    A2aAgentDefinition(
        name="echo",
        description="Echo agent that returns user input with an A2A task lifecycle",
        path="/a2a/echo",
        skill_id="echo",
        skill_name="Echo",
        skill_description="Echo user text back as an A2A task result",
        examples=("hello", "ping"),
        sample_message="hello a2a",
    ),
    A2aAgentDefinition(
        name="qa",
        description="LLM-powered Q&A agent exposed via the A2A protocol",
        path="/a2a/qa",
        skill_id="qa",
        skill_name="Q&A",
        skill_description="Answer general questions using the configured LLM",
        examples=(
            "What is LangGraph?",
            "Explain agent-to-agent protocols briefly.",
        ),
        sample_message="What is LangGraph in one sentence?",
        requires_llm=True,
    ),
)

A2A_AGENT_MAP: dict[str, A2aAgentDefinition] = {
    definition.name: definition for definition in A2A_AGENT_DEFINITIONS
}
