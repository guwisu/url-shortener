import json

from redis.asyncio import Redis


class LinkCache:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "link:"

    async def get(self, code: str) -> dict | None:
        link = await self.redis.get(f"{self.prefix}{code}")
        if not link:
            return None
        data = json.loads(link)
        return dict(data)

    async def set(self, code: str, data: dict, ttl: int):
        json_data = json.dumps(data)

        await self.redis.set(f"{self.prefix}{code}", json_data, ex=ttl)

    async def delete(self, code: str):
        await self.redis.delete(f"{self.prefix}{code}")
