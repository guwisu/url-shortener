import json
import logging
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

log = logging.getLogger(__name__)


class LinkCache:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "link:"

    async def get(self, code: str) -> dict[str, Any] | None:
        try:
            link = await self.redis.get(f"{self.prefix}{code}")
            if not link:
                return None
            data = json.loads(link)
            return dict(data)
        except RedisError as e:
            log.error(f"Redis error: {e}")
            return None

    async def set(self, code: str, data: dict[str, Any], ttl: int) -> None:
        try:
            json_data = json.dumps(data)
            await self.redis.set(f"{self.prefix}{code}", json_data, ex=ttl)
        except RedisError as e:
            log.error(f"Redis error: {e}")

    async def delete(self, code: str) -> None:
        try:
            await self.redis.delete(f"{self.prefix}{code}")
        except RedisError as e:
            log.error(f"Redis error: {e}")

    async def increment_clicks(self, code: str) -> None:
        try:
            await self.redis.incr(f"clicks:{code}")
        except RedisError as e:
            log.error(f"Redis error: {e}")

    async def get_clicks(self, code: str) -> int:
        try:
            values = await self.redis.mget(
                f"clicks:{code}", f"processing:clicks:{code}"
            )
            return sum(int(v) for v in values if v)
        except RedisError as e:
            log.error(f"Redis error: {e}")
            return 0

    async def get_clicks_batch(self, codes: list[str]) -> dict[str, int]:
        if not codes:
            return {}
        try:
            keys = [f"clicks:{c}" for c in codes] + [
                f"processing:clicks:{c}" for c in codes
            ]
            values = await self.redis.mget(keys)
            n = len(codes)
            result: dict[str, int] = {}
            for i, code in enumerate(codes):
                pending_raw = values[i]
                processing_raw = values[i + n]
                pending = int(pending_raw) if pending_raw is not None else 0
                processing = int(processing_raw) if processing_raw is not None else 0
                result[code] = pending + processing
            return result
        except RedisError as e:
            log.error(f"Redis error: {e}")
            return {}
