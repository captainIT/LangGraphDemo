from __future__ import annotations

import unittest
from unittest.mock import patch

from app.transport.mcp_client import McpClientTransport


class McpClientTransportTestCase(unittest.TestCase):
    def test_create_client_uses_registry_connections(self) -> None:
        with patch(
            "app.transport.mcp_client.build_stdio_connections",
            return_value={"math": {"transport": "stdio", "command": "python", "args": ["m.py"]}},
        ) as connections_mock, patch("app.transport.mcp_client.MultiServerMCPClient") as client_cls:
            transport = McpClientTransport(tool_name_prefix=False, timeout_seconds=12.0)
            transport.create_client(["math"])

        connections_mock.assert_called_once_with(["math"])
        client_cls.assert_called_once()

    def test_connection_summary(self) -> None:
        fake_connections = {
            "math": {"transport": "stdio", "command": "python", "args": ["m.py"]},
        }
        with patch("app.transport.mcp_client.build_stdio_connections", return_value=fake_connections):
            transport = McpClientTransport()
            summary = transport.connection_summary(["math"])
        self.assertEqual(summary[0]["server_name"], "math")
        self.assertEqual(summary[0]["transport"], "stdio")


if __name__ == "__main__":
    unittest.main()
