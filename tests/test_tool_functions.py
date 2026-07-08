from __future__ import annotations

import unittest

from app.utils.tool_functions import add_numbers, count_words, slugify_text


class ToolFunctionsTestCase(unittest.TestCase):
    def test_add_numbers(self) -> None:
        self.assertEqual(add_numbers.invoke({"a": 1.5, "b": 2.5}), 4.0)

    def test_count_words(self) -> None:
        self.assertEqual(count_words.invoke({"text": "hello world from test"}), 4)

    def test_slugify_text(self) -> None:
        self.assertEqual(
            slugify_text.invoke({"text": " LangGraph MCP Demo! "}),
            "langgraph-mcp-demo",
        )


if __name__ == "__main__":
    unittest.main()
