from __future__ import annotations

import unittest

from app.transport.mcp.registry import MCP_SERVER_MAP, build_stdio_connections


class McpRegistryTestCase(unittest.TestCase):
    def test_build_stdio_connections_default(self) -> None:
        connections = build_stdio_connections()
        self.assertTrue(connections)
        self.assertSetEqual(set(connections.keys()), set(MCP_SERVER_MAP.keys()))
        for config in connections.values():
            self.assertEqual(config["transport"], "stdio")
            self.assertTrue(config["args"])

    def test_build_stdio_connections_invalid_server(self) -> None:
        with self.assertRaises(ValueError):
            build_stdio_connections(["missing"])


if __name__ == "__main__":
    unittest.main()
