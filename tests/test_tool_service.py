from __future__ import annotations

import unittest

from app.service.tool_service import ToolService


class ToolServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_list_tools_sorted(self) -> None:
        service = ToolService()
        tools = service.list_tools()
        self.assertEqual(tools, sorted(tools))
        self.assertIn("add_numbers", tools)

    async def test_execute_success(self) -> None:
        service = ToolService()
        result = await service.execute("add_numbers", {"a": 2, "b": 3})
        self.assertEqual(result, 5)

    async def test_execute_unsupported_tool(self) -> None:
        service = ToolService()
        with self.assertRaises(ValueError):
            await service.execute("missing_tool", {})


if __name__ == "__main__":
    unittest.main()
