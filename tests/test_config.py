from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.config import get_settings


class SettingsTestCase(unittest.TestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_get_settings_uses_cache(self) -> None:
        get_settings.cache_clear()
        with patch.dict(os.environ, {"APP_NAME": "demo-a"}, clear=False):
            first = get_settings()
            second = get_settings()
        self.assertIs(first, second)

    def test_openai_fields_are_normalized(self) -> None:
        get_settings.cache_clear()
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "   ",
                "OPENAI_BASE_URL": " https://example.com/v1 ",
            },
            clear=False,
        ):
            settings = get_settings()
        self.assertIsNone(settings.openai_api_key)
        self.assertEqual(settings.openai_base_url, "https://example.com/v1")


if __name__ == "__main__":
    unittest.main()
