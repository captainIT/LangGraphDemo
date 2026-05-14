import json
import os
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import BaseTool
from app.transport.reasoning_echo_chat_openai import ReasoningEchoChatOpenAI


def _normalize_tool_call_args(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _tool_call_id(tool_call: dict[str, Any]) -> str:
    """ToolMessage requires a string; some providers emit null tool call ids."""
    call_id = tool_call.get("id")
    if call_id is None:
        return ""
    return str(call_id)


class LlmClient:
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        init_kwargs: dict[str, Any] = {"model": model, "temperature": 0}
        # Prefer explicit args; fall back to process env (OpenAI SDK reads os.environ only).
        effective_key = (api_key or os.getenv("OPENAI_API_KEY") or "").strip() or None
        effective_base = (base_url or os.getenv("OPENAI_BASE_URL") or "").strip() or None
        if effective_key:
            init_kwargs["api_key"] = effective_key
        if effective_base:
            init_kwargs["base_url"] = effective_base
        self._llm = ReasoningEchoChatOpenAI(**init_kwargs)

    async def ask(self, system_prompt: str, user_input: str) -> str:
        response = await self._llm.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ]
        )
        return str(response.content)

    async def stream_ask(self, system_prompt: str, user_input: str) -> AsyncIterator[str]:
        parser = StrOutputParser()
        chain = self._llm | parser
        async for chunk in chain.astream(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ]
        ):
            yield str(chunk)

    async def ask_with_tools(
        self,
        system_prompt: str,
        user_input: str,
        tools: list[BaseTool],
    ) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input),
        ]
        tool_llm = self._llm.bind_tools(tools)
        tool_map = {tool.name: tool for tool in tools}

        for _ in range(5):
            ai_message = await tool_llm.ainvoke(messages)
            messages.append(ai_message)
            tool_calls = getattr(ai_message, "tool_calls", [])
            if not tool_calls:
                return str(getattr(ai_message, "text", "") or ai_message.content or "")

            for tool_call in tool_calls:
                tool_name = str(tool_call["name"])
                tool_args = _normalize_tool_call_args(tool_call.get("args", {}))
                selected_tool = tool_map[tool_name]
                tool_result = await selected_tool.ainvoke(tool_args)
                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=_tool_call_id(tool_call),
                    )
                )

        final_response = await self._llm.ainvoke(messages)
        return str(getattr(final_response, "text", "") or final_response.content or "")

    async def ask_with_tools_and_trace(
        self,
        system_prompt: str,
        user_input: str,
        tools: list[BaseTool],
    ) -> tuple[str, list[dict[str, Any]]]:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input),
        ]
        tool_llm = self._llm.bind_tools(tools)
        tool_map = {tool.name: tool for tool in tools}
        trace: list[dict[str, Any]] = []

        for _ in range(5):
            ai_message = await tool_llm.ainvoke(messages)
            messages.append(ai_message)
            tool_calls = getattr(ai_message, "tool_calls", [])
            if not tool_calls:
                return (
                    str(getattr(ai_message, "text", "") or ai_message.content or ""),
                    trace,
                )

            for tool_call in tool_calls:
                tool_name = str(tool_call["name"])
                tool_args = _normalize_tool_call_args(tool_call.get("args", {}))
                selected_tool = tool_map[tool_name]
                tool_result = await selected_tool.ainvoke(tool_args)
                trace.append(
                    {
                        "tool_name": tool_name,
                        "arguments": tool_args,
                        "result": str(tool_result),
                    }
                )
                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=_tool_call_id(tool_call),
                    )
                )

        final_response = await self._llm.ainvoke(messages)
        return (
            str(getattr(final_response, "text", "") or final_response.content or ""),
            trace,
        )
