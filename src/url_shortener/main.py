import asyncio
import contextlib

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from url_shortener.api.handlers import setup_exception_handlers
from url_shortener.api.routers.health import router as health_router
from url_shortener.api.v1 import redirect_router, v1_router
from url_shortener.core.config import settings
from url_shortener.tasks.worker import click_sync_worker


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = Redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", decode_responses=True
    )
    app.state.redis = redis_client
    sync_task = asyncio.create_task(click_sync_worker(redis_client))
    yield
    sync_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await sync_task
    await redis_client.aclose()


app = FastAPI(title="url-shortener", version="0.1.0", lifespan=lifespan)

setup_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_headers=["*"],
    allow_methods=["*"],
)

app.include_router(health_router)
app.include_router(v1_router, prefix="/api")
app.include_router(redirect_router)


if __name__ == "__main__":
    uvicorn.run(app="url_shortener.main:app", reload=True)
