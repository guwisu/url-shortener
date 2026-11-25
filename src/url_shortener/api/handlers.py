from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from url_shortener.core.exceptions import (
    AliasAlreadyExists,
    InvalidCredentials,
    LinkDeactivated,
    LinkNotFound,
    ServiceUnavailable,
    UserAlreadyExists,
)


def _make_exception_handler(
    status_code: int, detail: str
) -> Callable[[Request, Exception], Coroutine[Any, Any, JSONResponse]]:
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": detail})

    return handler


def setup_exception_handlers(app: FastAPI) -> None:
    handlers: list[tuple[type[Exception], int, str]] = [
        (LinkNotFound, 404, "Link not found"),
        (LinkDeactivated, 410, "Link has been expired or been deactivated"),
        (UserAlreadyExists, 400, "Email already registered"),
        (InvalidCredentials, 401, "Invalid credentials"),
        (
            ServiceUnavailable,
            503,
            "Service temporarily unavailable. Please try again.",
        ),
        (AliasAlreadyExists, 409, "Alias is already taken"),
    ]
    for exc_type, status_code, detail in handlers:
        app.add_exception_handler(
            exc_type, _make_exception_handler(status_code, detail)
        )

    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
