from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.service.a2a_service import A2aService


class _FakeTransport:
    async def fetch_agent_card_dict(self, path: str) -> dict:
        return {"path": path, "name": "demo"}

    async def send_text_message(self, path: str, input_text: str) -> tuple[list[str], dict]:
        return [f"reply:{input_text}"], {"path": path}


class A2aServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_list_agents_without_api_key_marks_llm_agent_unmounted(self) -> None:
        service = A2aService(
            transport=_FakeTransport(),
            settings=SimpleNamespace(openai_api_key=None),
        )
        agents = service.list_agents()
        by_name = {item.name: item for item in agents}
        self.assertTrue(by_name["echo"].mounted)
        self.assertFalse(by_name["qa"].mounted)

    async def test_get_agent_card_success(self) -> None:
        service = A2aService(
            transport=_FakeTransport(),
            settings=SimpleNamespace(openai_api_key="sk-test"),
        )
        card = await service.get_agent_card("echo")
        self.assertEqual(card["path"], "/a2a/echo")

    async def test_send_message_success(self) -> None:
        service = A2aService(
            transport=_FakeTransport(),
            settings=SimpleNamespace(openai_api_key="sk-test"),
        )
        result = await service.send_message("echo", "hello")
        self.assertEqual(result.output_text, "reply:hello")

    async def test_resolve_unknown_agent(self) -> None:
        service = A2aService(
            transport=_FakeTransport(),
            settings=SimpleNamespace(openai_api_key="sk-test"),
        )
        with self.assertRaises(ValueError):
            await service.get_agent_card("missing")


if __name__ == "__main__":
    unittest.main()
