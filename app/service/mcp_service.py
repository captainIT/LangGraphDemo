"""MCP orchestration: discovery, invocation, and full-flow smoke tests."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.tools import BaseTool

from app.schemas.mcp import (
    McpFlowStep,
    McpFullFlowResult,
    McpServerInfo,
    McpToolInfo,
    McpToolInvokeResult,
)
from app.transport.mcp.registry import MCP_SERVER_DEFINITIONS, MCP_SERVER_MAP
from app.transport.mcp_client import McpClientTransport

logger = logging.getLogger(__name__)

_SAMPLE_INVOCATIONS: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "math": [
        ("add_numbers", {"a": 10.0, "b": 32.0}),
        ("multiply_numbers", {"a": 6.0, "b": 7.0}),
    ],
    "time": [
        ("get_current_utc_time", {}),
    ],
    "text": [
        ("count_words", {"text": "hello world from mcp"}),
        ("slugify_text", {"text": "LangGraph MCP Demo"}),
    ],
}


class McpService:
    def __init__(self, transport: McpClientTransport) -> None:
        self._transport = transport

    def list_servers(self) -> list[McpServerInfo]:
        return [
            McpServerInfo(
                name=definition.name,
                description=definition.description,
                transport="stdio",
                tool_names=list(definition.tool_names),
            )
            for definition in MCP_SERVER_DEFINITIONS
        ]

    async def list_tools(self, server_names: list[str] | None = None) -> list[McpToolInfo]:
        client = self._transport.create_client(server_names)
        tools = await asyncio.wait_for(
            client.get_tools(),
            timeout=self._transport.timeout_seconds,
        )
        return [self._to_tool_info(tool) for tool in tools]

    async def invoke_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        server_name: str | None = None,
    ) -> McpToolInvokeResult:
        client = self._transport.create_client([server_name] if server_name else None)
        tools = await asyncio.wait_for(
            client.get_tools(server_name=server_name),
            timeout=self._transport.timeout_seconds,
        )
        selected = self._resolve_tool(tools, tool_name)
        if selected is None:
            available = ", ".join(sorted(tool.name for tool in tools))
            raise ValueError(f"Unsupported MCP tool: {tool_name}. Available: {available}")

        result = await asyncio.wait_for(
            selected.ainvoke(arguments),
            timeout=self._transport.timeout_seconds,
        )
        return McpToolInvokeResult(
            tool_name=selected.name,
            arguments=arguments,
            result=result,
        )

    async def run_full_flow(
        self,
        server_names: list[str] | None = None,
        include_tool_invocations: bool = True,
    ) -> McpFullFlowResult:
        selected_servers = server_names or list(MCP_SERVER_MAP.keys())
        steps: list[McpFlowStep] = []
        invocations: list[McpToolInvokeResult] = []

        steps.append(
            McpFlowStep(
                step="resolve_servers",
                status="ok",
                detail={"servers": selected_servers},
            )
        )

        client = self._transport.create_client(selected_servers)
        steps.append(
            McpFlowStep(
                step="connect_stdio",
                status="ok",
                detail={"connections": self._transport.connection_summary(selected_servers)},
            )
        )

        tools = await asyncio.wait_for(
            client.get_tools(),
            timeout=self._transport.timeout_seconds,
        )
        tool_infos = [self._to_tool_info(tool) for tool in tools]
        steps.append(
            McpFlowStep(
                step="list_tools",
                status="ok",
                detail={"tool_count": len(tool_infos), "tools": [tool.name for tool in tool_infos]},
            )
        )

        if include_tool_invocations:
            for server in selected_servers:
                for local_tool_name, arguments in _SAMPLE_INVOCATIONS.get(server, []):
                    prefixed_name = f"{server}_{local_tool_name}"
                    selected = self._resolve_tool(tools, prefixed_name, local_tool_name)
                    if selected is None:
                        steps.append(
                            McpFlowStep(
                                step="invoke_tool",
                                status="error",
                                detail={
                                    "server_name": server,
                                    "tool_name": local_tool_name,
                                    "error": "tool not found after discovery",
                                },
                            )
                        )
                        continue

                    try:
                        result = await asyncio.wait_for(
                            selected.ainvoke(arguments),
                            timeout=self._transport.timeout_seconds,
                        )
                        invocations.append(
                            McpToolInvokeResult(
                                tool_name=selected.name,
                                arguments=arguments,
                                result=result,
                            )
                        )
                        steps.append(
                            McpFlowStep(
                                step="invoke_tool",
                                status="ok",
                                detail={
                                    "server_name": server,
                                    "tool_name": selected.name,
                                    "arguments": arguments,
                                    "result": result,
                                },
                            )
                        )
                    except Exception as exc:
                        logger.exception(
                            "mcp sample invocation failed",
                            extra={"server_name": server, "tool_name": local_tool_name},
                        )
                        steps.append(
                            McpFlowStep(
                                step="invoke_tool",
                                status="error",
                                detail={
                                    "server_name": server,
                                    "tool_name": local_tool_name,
                                    "error": str(exc),
                                },
                            )
                        )

        steps.append(McpFlowStep(step="complete", status="ok", detail={}))
        return McpFullFlowResult(
            servers=selected_servers,
            tools=tool_infos,
            invocations=invocations,
            steps=steps,
        )

    async def run_server_flow(
        self,
        server_name: str,
        include_tool_invocations: bool = True,
    ) -> McpFullFlowResult:
        if server_name not in MCP_SERVER_MAP:
            raise ValueError(f"Unsupported MCP server: {server_name}")
        return await self.run_full_flow(
            server_names=[server_name],
            include_tool_invocations=include_tool_invocations,
        )

    @staticmethod
    def _to_tool_info(tool: BaseTool) -> McpToolInfo:
        server_name = None
        if "_" in tool.name:
            server_name = tool.name.split("_", 1)[0]
        args_schema = getattr(tool, "args_schema", None)
        if args_schema is None:
            input_schema: dict[str, Any] = {}
        elif isinstance(args_schema, dict):
            input_schema = args_schema
        elif hasattr(args_schema, "model_json_schema"):
            input_schema = args_schema.model_json_schema()
        else:
            input_schema = {}
        return McpToolInfo(
            name=tool.name,
            description=tool.description or "",
            server_name=server_name,
            input_schema=input_schema,
        )

    @staticmethod
    def _resolve_tool(
        tools: list[BaseTool],
        preferred_name: str,
        fallback_name: str | None = None,
    ) -> BaseTool | None:
        by_name = {tool.name: tool for tool in tools}
        if preferred_name in by_name:
            return by_name[preferred_name]
        if fallback_name and fallback_name in by_name:
            return by_name[fallback_name]
        return None
