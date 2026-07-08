from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.common import ApiResponse, ErrorDetail

logger = logging.getLogger(__name__)


def _error_code_from_status(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).name.lower()
    except ValueError:
        return "unknown_error"


def _build_error_response(
    *,
    status_code: int,
    message: str,
    detail: str,
    code: str,
) -> JSONResponse:
    payload = ApiResponse(
        success=False,
        message=message,
        error=ErrorDetail(code=code, detail=detail),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return _build_error_response(
            status_code=exc.status_code,
            message="request_failed",
            detail=detail,
            code=_error_code_from_status(exc.status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _build_error_response(
            status_code=422,
            message="validation_failed",
            detail=str(exc),
            code="validation_error",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application exception")
        return _build_error_response(
            status_code=500,
            message="internal_server_error",
            detail="An unexpected error occurred",
            code="internal_server_error",
        )
