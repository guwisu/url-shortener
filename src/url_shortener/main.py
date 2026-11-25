import contextlib
import logging
from typing import Any

import uvicorn
from aiokafka.producer.producer import AIOKafkaProducer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient
from redis.asyncio import Redis

from url_shortener.api.handlers import setup_exception_handlers
from url_shortener.api.routers.health import router as health_router
from url_shortener.api.v1 import redirect_router, v1_router
from url_shortener.core.config import settings
from url_shortener.core.rate_limit import limiter


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = Redis.from_url(url=settings.redis_url, decode_responses=True)
    app.state.redis = redis_client

    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
    )
    await kafka_producer.start()
    app.state.kafka_producer = kafka_producer

    mongo_client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        settings.mongo_url
    )
    app.state.mongo_client = mongo_client

    yield

    await mongo_client.close()
    await kafka_producer.stop()
    await redis_client.aclose()


logging.basicConfig(level=logging.INFO)

app = FastAPI(title="url-shortener", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter

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
