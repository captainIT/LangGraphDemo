from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.service.mcp_service import McpService


class _FakeTool:
    def __init__(self, name: str, result: object, description: str = "desc") -> None:
        self.name = name
        self.description = description
        self.args_schema = {}
        self._result = result

    async def ainvoke(self, arguments: dict) -> object:
        _ = arguments
        return self._result


class _FakeClient:
    def __init__(self, tools: list[_FakeTool]) -> None:
        self._tools = tools

    async def get_tools(self, server_name: str | None = None) -> list[_FakeTool]:
        _ = server_name
        return self._tools


class _FakeTransport:
    timeout_seconds = 5.0

    def __init__(self, tools: list[_FakeTool]) -> None:
        self._tools = tools

    def create_client(self, server_names: list[str] | None = None) -> _FakeClient:
        _ = server_names
        return _FakeClient(self._tools)

    def connection_summary(self, server_names: list[str]) -> list[dict]:
        return [{"server_name": name, "transport": "stdio"} for name in server_names]


class McpServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_invoke_tool_success(self) -> None:
        transport = _FakeTransport([_FakeTool("math_add_numbers", 42)])
        service = McpService(transport=transport)

        result = await service.invoke_tool("math_add_numbers", {"a": 1, "b": 2})
        self.assertEqual(result.tool_name, "math_add_numbers")
        self.assertEqual(result.result, 42)

    async def test_invoke_tool_unsupported(self) -> None:
        transport = _FakeTransport([_FakeTool("math_add_numbers", 42)])
        service = McpService(transport=transport)

        with self.assertRaises(ValueError):
            await service.invoke_tool("missing", {})

    async def test_list_tools(self) -> None:
        transport = _FakeTransport([_FakeTool("math_add_numbers", 3)])
        service = McpService(transport=transport)
        tools = await service.list_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0].name, "math_add_numbers")

    async def test_run_server_flow_invalid_server(self) -> None:
        service = McpService(transport=_FakeTransport([]))
        with self.assertRaises(ValueError):
            await service.run_server_flow("missing")


if __name__ == "__main__":
    unittest.main()
