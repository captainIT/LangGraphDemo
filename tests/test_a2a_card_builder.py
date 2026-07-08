from __future__ import annotations

import unittest

from app.transport.a2a.card_builder import agent_card_url, build_agent_card
from app.transport.a2a.registry import A2A_AGENT_MAP


class A2aCardBuilderTestCase(unittest.TestCase):
    def test_build_agent_card(self) -> None:
        definition = A2A_AGENT_MAP["echo"]
        card = build_agent_card(definition, "http://127.0.0.1:8000/")
        self.assertEqual(card.name, "Echo Agent")
        self.assertEqual(card.skills[0].id, "echo")
        self.assertTrue(card.supported_interfaces)

    def test_agent_card_url(self) -> None:
        definition = A2A_AGENT_MAP["qa"]
        self.assertEqual(
            agent_card_url(definition),
            "/a2a/qa/.well-known/agent-card.json",
        )


if __name__ == "__main__":
    unittest.main()
