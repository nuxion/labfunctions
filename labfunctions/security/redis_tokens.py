from typing import Optional, Union

from redis.asyncio import Redis

from labfunctions.redis_conn import create_pool

from .base import TokenStoreSpec
from .utils import generate_token


class RedisTokenStore(TokenStoreSpec):
    def __init__(self, redis: Union[Redis, str], namespace: str = "rtkn"):
        if isinstance(redis, str):
            _redis = create_pool(redis, decode_responses=True)
        else:
            _redis = redis
        self.redis: Redis = _redis
        self.ns = namespace

    async def put(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        await self.redis.set(f"{self.ns}:{key}", value)
        return True

    async def get(self, key: str) -> str:
        val = await self.redis.get(f"{self.ns}:{key}")
        value = val
        if not isinstance(val, str) and val:
            value = val.decode("utf-8")

        return value

    async def delete(self, key: str):
        await self.redis.delete(f"{self.ns}:{key}")

    @staticmethod
    def generate(sign: Optional[str] = None) -> str:
        return generate_token()
