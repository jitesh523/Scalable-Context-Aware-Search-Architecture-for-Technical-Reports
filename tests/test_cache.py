import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from src.cache.redis_client import RedisClient
from src.cache.decorators import cache_response
from config.settings import settings

@pytest.mark.asyncio
async def test_redis_client_mock_mode():
    """Test Redis client in mock mode."""
    # Enable mock mode
    settings.features.mock_mode = True
    client = RedisClient()
    
    # Test Set
    await client.set("test_key", {"foo": "bar"})
    assert client.mock_cache["test_key"] == {"foo": "bar"}
    
    # Test Get
    result = await client.get("test_key")
    assert result == {"foo": "bar"}
    
    # Test Miss
    result = await client.get("missing_key")
    assert result is None

@pytest.mark.asyncio
async def test_redis_client_real_connection():
    """Test Redis client connection logic (mocked redis lib)."""
    settings.features.mock_mode = False
    
    with patch("redis.asyncio.Redis") as mock_redis_cls:
        mock_redis = AsyncMock()
        mock_redis_cls.return_value = mock_redis
        mock_redis.get.return_value = json.dumps({"data": "cached"})
        mock_redis.set.return_value = True
        
        client = RedisClient()
        # Force reset client for test
        client.client = None
        
        # Test Get
        result = await client.get("real_key")
        assert result == {"data": "cached"}
        mock_redis.get.assert_called_once_with("real_key")
        
        # Test Set
        await client.set("real_key", {"data": "new"})
        mock_redis.set.assert_called_once()

@pytest.mark.asyncio
async def test_cache_decorator():
    """Test cache decorator logic."""
    settings.features.mock_mode = True
    client = RedisClient()
    client.mock_cache = {} # Reset cache
    
    # Mock function to decorate
    mock_func = AsyncMock(return_value={"result": "computed"})
    
    @cache_response(ttl=60, prefix="test")
    async def decorated_func(query: str):
        return await mock_func(query)
    
    # First call - should compute and cache
    result1 = await decorated_func(query="hello")
    assert result1 == {"result": "computed"}
    assert mock_func.call_count == 1
    
    # Check cache
    cache_key = client.generate_key("test", query="hello")
    assert client.mock_cache.get(cache_key) == {"result": "computed"}
    
    # Second call - should return from cache
    result2 = await decorated_func(query="hello")
    assert result2 == {"result": "computed"}
    assert mock_func.call_count == 1 # Should not increment
