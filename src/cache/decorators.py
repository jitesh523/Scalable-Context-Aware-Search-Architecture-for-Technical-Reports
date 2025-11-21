import functools
import json
from typing import Callable, Any
from fastapi import Request, Response
from src.cache.redis_client import RedisClient
from config.settings import settings

redis_client = RedisClient()

def cache_response(ttl: int = 3600, prefix: str = "api"):
    """
    Decorator to cache FastAPI response.
    
    Args:
        ttl: Time to live in seconds
        prefix: Cache key prefix
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip caching if disabled via settings (optional future feature)
            
            # Extract request object to get query params if needed
            # For simplicity, we'll use kwargs for key generation
            
            # Generate cache key
            cache_key = redis_client.generate_key(prefix, **kwargs)
            
            # Try to get from cache
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                return cached_data
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result (assuming result is serializable)
            # Note: If result is a Pydantic model, we might need to dump it
            if hasattr(result, "model_dump"):
                data_to_cache = result.model_dump()
            elif hasattr(result, "dict"):
                data_to_cache = result.dict()
            else:
                data_to_cache = result
                
            await redis_client.set(cache_key, data_to_cache, ttl=ttl)
            
            return result
        return wrapper
    return decorator
