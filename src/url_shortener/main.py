from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import asyncio as aioredis

from url_shortener.api.routers.health import router as health_router
from url_shortener.api.v1 import redirect_router, v1_router
from url_shortener.core.config import settings

redis_client: aioredis.Redis | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client

    redis_client = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        decode_responses=True
    )

    yield

    await redis_client.close()
    
    
app = FastAPI(
    title="url-shortener",
    version="0.1.0",
    lifespan=lifespan
)

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
