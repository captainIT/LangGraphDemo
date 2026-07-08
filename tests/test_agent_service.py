from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.agent import AgentType
from app.service.agent_service import AgentService


class AgentServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_run_agent_delegates_to_run_agent_turn(self) -> None:
        fake_llm = AsyncMock()
        fake_graph = AsyncMock()
        fake_graph.ainvoke = AsyncMock(return_value={"steps": [], "output_text": "done"})

        with patch("app.service.agent_service.build_collaborative_workflow_graph", return_value=fake_graph), patch(
            "app.service.agent_service.run_agent_turn",
            new=AsyncMock(return_value="ok"),
        ) as run_mock:
            service = AgentService(fake_llm)
            result = await service.run_agent(AgentType.qa_agent, "hello")

        self.assertEqual(result, "ok")
        run_mock.assert_awaited_once_with(fake_llm, AgentType.qa_agent, "hello")

    async def test_run_collaborative_workflow(self) -> None:
        fake_llm = AsyncMock()
        fake_graph = MagicMock()
        fake_graph.ainvoke = AsyncMock(
            return_value={"steps": ["route", "answer"], "output_text": "final"}
        )

        with patch("app.service.agent_service.build_collaborative_workflow_graph", return_value=fake_graph):
            service = AgentService(fake_llm)
            steps, output = await service.run_collaborative_workflow("input")

        self.assertEqual(steps, ["route", "answer"])
        self.assertEqual(output, "final")

    async def test_stream_agent_yields_chunks(self) -> None:
        async def _stream(prompt: str, text: str):
            _ = (prompt, text)
            for item in ["a", "b"]:
                yield item

        fake_llm = MagicMock()
        fake_llm.stream_ask = _stream
        fake_graph = MagicMock()
        fake_graph.ainvoke = AsyncMock(return_value={"steps": [], "output_text": ""})

        with patch("app.service.agent_service.build_collaborative_workflow_graph", return_value=fake_graph):
            service = AgentService(fake_llm)
            chunks = [item async for item in service.stream_agent(AgentType.qa_agent, "hello")]

        self.assertEqual(chunks, ["a", "b"])


if __name__ == "__main__":
    unittest.main()
