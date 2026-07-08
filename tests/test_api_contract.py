from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiContractTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_returns_standard_response(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["message"], "ok")
        self.assertEqual(payload["data"]["status"], "healthy")
        self.assertIsNone(payload["error"])

    def test_http_exception_is_wrapped_in_api_response(self) -> None:
        response = self.client.post(
            "/api/v1/agents/run-with-trace",
            json={"agent_type": "qa_agent", "input_text": "hello"},
        )
        self.assertEqual(response.status_code, 400)

        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["message"], "request_failed")
        self.assertEqual(payload["error"]["code"], "bad_request")
        self.assertIn("tool_agent only", payload["error"]["detail"])

    def test_validation_exception_is_wrapped_in_api_response(self) -> None:
        response = self.client.post(
            "/api/v1/tools",
            json={},
        )
        self.assertEqual(response.status_code, 422)

        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["message"], "validation_failed")
        self.assertEqual(payload["error"]["code"], "validation_error")
        self.assertIn("tool_name", payload["error"]["detail"])


if __name__ == "__main__":
    unittest.main()
