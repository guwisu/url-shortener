from typing import Annotated, Any

from aiokafka import AIOKafkaProducer
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from url_shortener.core.config import settings
from url_shortener.core.security import decode_access_token
from url_shortener.db.session import get_db
from url_shortener.models import User
from url_shortener.repositories import LinkRepository
from url_shortener.repositories.users import UserRepository
from url_shortener.services import AuthService, LinkService
from url_shortener.services.analytics import AnalyticsService
from url_shortener.services.cache import LinkCache
from url_shortener.services.events import EventPublisher


def get_link_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LinkRepository:
    return LinkRepository(session)


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_link_cache(redis: Annotated[Redis, Depends(get_redis)]) -> LinkCache:
    return LinkCache(redis)


def get_link_service(
    repository: Annotated[LinkRepository, Depends(get_link_repository)],
    cache: Annotated[LinkCache, Depends(get_link_cache)],
) -> LinkService:
    return LinkService(repository, cache)


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    return UserRepository(session)


def get_auth_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(repository)


oauth2_scheme = HTTPBearer()


async def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    decoded_token = decode_access_token(token.credentials)
    if decoded_token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await repo.get_by_id(decoded_token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_kafka_producer(request: Request) -> AIOKafkaProducer:
    return request.app.state.kafka_producer


def get_event_publisher(
    producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)],
) -> EventPublisher:
    return EventPublisher(producer=producer, topic=settings.KAFKA_CLICK_TOPIC)


def get_click_events_collection(request: Request) -> AsyncCollection:
    mongo_client: AsyncMongoClient[dict[str, Any]] = request.app.state.mongo_client
    return mongo_client[settings.MONGO_DB]["click_events"]


def get_analytics_service(
    link_repo: Annotated[LinkRepository, Depends(get_link_repository)],
    collection: Annotated[AsyncCollection, Depends(get_click_events_collection)],
) -> AnalyticsService:
    return AnalyticsService(link_repo, collection)
