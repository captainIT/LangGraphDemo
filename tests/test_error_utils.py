from __future__ import annotations

import unittest

from fastapi import HTTPException

from app.api.error_utils import raise_bad_request, raise_internal_server_error


class ErrorUtilsTestCase(unittest.TestCase):
    def test_raise_bad_request(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            raise_bad_request(ValueError("bad input"))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "bad input")

    def test_raise_internal_server_error(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            raise_internal_server_error(RuntimeError("x"), "failed")
        self.assertEqual(ctx.exception.status_code, 500)
        self.assertEqual(ctx.exception.detail, "failed")


if __name__ == "__main__":
    unittest.main()
