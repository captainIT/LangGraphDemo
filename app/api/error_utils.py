from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException, status


def raise_bad_request(exc: ValueError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    ) from exc


def raise_internal_server_error(exc: Exception, detail: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
    ) from exc
