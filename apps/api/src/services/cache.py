import json
from typing import Optional, Union

import redis.asyncio as redis
from pydantic import BaseModel


class RedisCache:
    """Redis cache wrapper"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        value = await self.redis.get(key)
        return value.decode("utf-8") if value else None

    async def set(
        self, key: str, value: Union[str, int, float, dict, BaseModel], expire: Optional[int] = None
    ):
        """Set value in cache"""
        if isinstance(value, BaseModel):
            value = value.model_dump_json()
        elif isinstance(value, dict):
            value = json.dumps(value)

        await self.redis.set(key, value, ex=expire)

    async def delete(self, key: str):
        """Delete value from cache"""
        await self.redis.delete(key)

    async def incr(self, key: str) -> int:
        """Increment counter"""
        return await self.redis.incr(key)

    async def expire(self, key: str, seconds: int):
        """Set key expiration"""
        await self.redis.expire(key, seconds)

    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from cache"""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None


class CacheService:
    """Service for handling caching logic"""

    def __init__(self, cache: RedisCache):
        self.cache = cache

    async def get_experiment_config(self, experiment_id: str) -> Optional[dict]:
        """Get experiment configuration from cache"""
        key = f"experiment:config:{experiment_id}"
        return await self.cache.get_json(key)

    async def set_experiment_config(self, experiment_id: str, config: dict, expire: int = 3600):
        """Cache experiment configuration"""
        key = f"experiment:config:{experiment_id}"
        await self.cache.set(key, config, expire)

    async def get_variant_assignment(self, experiment_id: str, user_id: str) -> Optional[dict]:
        """Get cached variant assignment"""
        key = f"assignment:{experiment_id}:{user_id}"
        return await self.cache.get_json(key)

    async def set_variant_assignment(
        self, experiment_id: str, user_id: str, assignment: dict, expire: int = 86400  # 24 hours
    ):
        """Cache variant assignment"""
        key = f"assignment:{experiment_id}:{user_id}"
        await self.cache.set(key, assignment, expire)

    async def get_metric_stats(self, experiment_id: str, metric_name: str) -> Optional[dict]:
        """Get cached metric statistics"""
        key = f"metric:stats:{experiment_id}:{metric_name}"
        return await self.cache.get_json(key)

    async def set_metric_stats(
        self, experiment_id: str, metric_name: str, stats: dict, expire: int = 300  # 5 minutes
    ):
        """Cache metric statistics"""
        key = f"metric:stats:{experiment_id}:{metric_name}"
        await self.cache.set(key, stats, expire)
