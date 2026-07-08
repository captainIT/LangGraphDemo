from __future__ import annotations

import unittest

from app.schemas.agent import AgentType
from app.service.agent_prompts import build_system_prompt, default_route_intent, route_user_intent


class _FakeLlm:
    def __init__(self, output: str) -> None:
        self._output = output

    async def ask(self, *, system_prompt: str, user_input: str) -> str:
        _ = (system_prompt, user_input)
        return self._output


class AgentPromptsTestCase(unittest.IsolatedAsyncioTestCase):
    def test_build_system_prompt(self) -> None:
        prompt = build_system_prompt(AgentType.qa_agent)
        self.assertIn("Q&A assistant", prompt)

    def test_default_route_intent(self) -> None:
        result = default_route_intent()
        self.assertEqual(result["primary_agent"], AgentType.qa_agent.value)
        self.assertFalse(result["should_summarize"])
        self.assertFalse(result["should_translate"])

    async def test_route_user_intent_returns_parsed_json(self) -> None:
        llm = _FakeLlm('{"primary_agent":"planner_agent","should_summarize":true}')
        result = await route_user_intent(llm, "plan this")
        self.assertEqual(result["primary_agent"], "planner_agent")

    async def test_route_user_intent_fallback_on_invalid_json(self) -> None:
        llm = _FakeLlm("not json")
        result = await route_user_intent(llm, "hello")
        self.assertEqual(result, default_route_intent())


if __name__ == "__main__":
    unittest.main()
