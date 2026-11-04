from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import asyncio as aioredis

from url_shortener.api.routers.health import router as health_router
from url_shortener.api.v1 import redirect_router, v1_router
from url_shortener.core.config import settings
from url_shortener.core.exceptions import (
    InvalidCredentials,
    LinkDeactivated,
    LinkNotFound,
    ServiceUnavailable,
    UserAlreadyExists,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = aioredis.Redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", decode_responses=True
    )
    app.state.redis = redis_client
    yield
    await redis_client.aclose()


app = FastAPI(title="url-shortener", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_headers=["*"],
    allow_methods=["*"],
)

app.include_router(health_router)
app.include_router(v1_router, prefix="/api")
app.include_router(redirect_router)


@app.exception_handler(LinkNotFound)
async def link_not_found_handler(request: Request, exc: LinkNotFound):
    return JSONResponse(status_code=404, content={"detail": "Link not found"})


@app.exception_handler(LinkDeactivated)
async def link_deactivated_handler(request: Request, exc: LinkDeactivated):
    return JSONResponse(
        status_code=410, content={"detail": "Link has been expired or been deactivated"}
    )


@app.exception_handler(UserAlreadyExists)
async def user_already_exists_handler(request: Request, exc: UserAlreadyExists):
    return JSONResponse(status_code=400, content={"detail": "Email already registered"})


@app.exception_handler(InvalidCredentials)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentials):
    return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})


@app.exception_handler(ServiceUnavailable)
async def service_unavailable_handler(request: Request, exc: ServiceUnavailable):
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable. Please try again."},
    )


if __name__ == "__main__":
    uvicorn.run(app="url_shortener.main:app", reload=True)
