from __future__ import annotations

import json
import logging
import unittest

from app.utils.logger import JsonFormatter, setup_logging


class LoggerTestCase(unittest.TestCase):
    def test_json_formatter_outputs_expected_fields(self) -> None:
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="demo.logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="hello",
            args=(),
            exc_info=None,
        )
        payload = json.loads(formatter.format(record))
        self.assertEqual(payload["level"], "INFO")
        self.assertEqual(payload["logger"], "demo.logger")
        self.assertEqual(payload["message"], "hello")
        self.assertIn("timestamp", payload)

    def test_setup_logging_sets_root_level(self) -> None:
        setup_logging("debug")
        root = logging.getLogger()
        self.assertEqual(root.level, logging.DEBUG)
        self.assertEqual(len(root.handlers), 1)


if __name__ == "__main__":
    unittest.main()
