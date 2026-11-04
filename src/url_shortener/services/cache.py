import json
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

log = logging.getLogger(__name__)


class LinkCache:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "link:"

    async def get(self, code: str) -> dict | None:
        try:
            link = await self.redis.get(f"{self.prefix}{code}")
            if not link:
                return None
            data = json.loads(link)
            return dict(data)
        except RedisError as e:
            log.error(f"Redis error: {e}")
            return None

    async def set(self, code: str, data: dict, ttl: int):
        try:
            json_data = json.dumps(data)

            await self.redis.set(f"{self.prefix}{code}", json_data, ex=ttl)
        except RedisError as e:
            log.error(f"Redis error: {e}")

    async def delete(self, code: str):
        try:
            await self.redis.delete(f"{self.prefix}{code}")
        except RedisError as e:
            log.error(f"Redis error: {e}")

    async def increment_clicks(self, code: str):
        try:
            await self.redis.incr(f"clicks:{code}")
        except RedisError as e:
            log.error(f"Redis error: {e}")

    async def get_clicks(self, code: str):
        try:
            clicks = await self.redis.get(f"clicks:{code}")
            if clicks:
                return int(clicks)
            return 0
        except RedisError as e:
            log.error(f"Redis error: {e}")
            return 0
