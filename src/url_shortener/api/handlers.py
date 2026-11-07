from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from url_shortener.core.exceptions import (
    InvalidCredentials,
    LinkDeactivated,
    LinkNotFound,
    ServiceUnavailable,
    UserAlreadyExists,
)


async def link_not_found_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=404, content={"detail": "Link not found"})


async def link_deactivated_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=410, content={"detail": "Link has been expired or been deactivated"}
    )


async def user_already_exists_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=400, content={"detail": "Email already registered"})


async def invalid_credentials_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})


async def service_unavailable_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable. Please try again."},
    )


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(LinkNotFound, link_not_found_handler)
    app.add_exception_handler(LinkDeactivated, link_deactivated_handler)
    app.add_exception_handler(UserAlreadyExists, user_already_exists_handler)
    app.add_exception_handler(InvalidCredentials, invalid_credentials_handler)
    app.add_exception_handler(ServiceUnavailable, service_unavailable_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
