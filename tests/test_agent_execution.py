from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from app.schemas.agent import AgentType
from app.service.agent_execution import run_agent_turn


class AgentExecutionTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_run_agent_turn_uses_tools_for_tool_agent(self) -> None:
        llm = AsyncMock()
        llm.ask_with_tools = AsyncMock(return_value="tool-result")

        result = await run_agent_turn(llm, AgentType.tool_agent, "2+2")

        self.assertEqual(result, "tool-result")
        llm.ask_with_tools.assert_awaited_once()
        llm.ask.assert_not_called()

    async def test_run_agent_turn_uses_prompt_for_other_agents(self) -> None:
        llm = AsyncMock()
        llm.ask = AsyncMock(return_value="qa-result")

        result = await run_agent_turn(llm, AgentType.qa_agent, "what is this")

        self.assertEqual(result, "qa-result")
        llm.ask.assert_awaited_once()
        llm.ask_with_tools.assert_not_called()


if __name__ == "__main__":
    unittest.main()
