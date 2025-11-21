import json
import hashlib
from typing import Any, Optional, Union
import redis.asyncio as redis
from config.settings import settings

class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.mock_cache = {}
        return cls._instance

    async def connect(self):
        """Initialize Redis connection."""
        if settings.features.mock_mode:
            return

        if not self.client:
            self.client = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                db=settings.redis.db,
                password=settings.redis.password,
                decode_responses=True
            )

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        if settings.features.mock_mode:
            return self.mock_cache.get(key)

        if not self.client:
            await self.connect()
        
        try:
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        if settings.features.mock_mode:
            self.mock_cache[key] = value
            return True

        if not self.client:
            await self.connect()

        try:
            return await self.client.set(
                key, 
                json.dumps(value), 
                ex=ttl
            )
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    def generate_key(self, prefix: str, **kwargs) -> str:
        """Generate a unique cache key based on arguments."""
        sorted_kwargs = dict(sorted(kwargs.items()))
        key_string = f"{prefix}:{json.dumps(sorted_kwargs, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()

    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
