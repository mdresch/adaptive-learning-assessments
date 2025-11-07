"""
Cache Manager

Redis-based caching system for BKT competency data to optimize performance
for concurrent users and real-time updates.
"""

import json
import logging
from typing import Any, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
import pickle

from ..models.bkt_models import LearnerCompetency, BKTParameters

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis-based cache manager for BKT data with serialization support.
    Optimized for high-frequency reads and concurrent access.
    """
    
    def __init__(
        self, 
        redis_url: str = "redis://localhost:6379",
        key_prefix: str = "bkt:",
        default_ttl: int = 300
    ):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.redis_client: Optional[redis.Redis] = None
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False  # We'll handle encoding ourselves for complex objects
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Cache manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with automatic deserialization.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            if not self.redis_client:
                return None
            
            cache_key = self._make_key(key)
            data = await self.redis_client.get(cache_key)
            
            if data is None:
                return None
            
            # Try to deserialize as Pydantic model first, then fallback to pickle
            try:
                return self._deserialize_pydantic(data)
            except:
                return pickle.loads(data)
                
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with automatic serialization.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                return False
            
            cache_key = self._make_key(key)
            ttl = ttl or self.default_ttl
            
            # Serialize based on type
            if hasattr(value, 'dict'):  # Pydantic model
                data = self._serialize_pydantic(value)
            else:
                data = pickle.dumps(value)
            
            await self.redis_client.setex(cache_key, ttl, data)
            return True
            
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                return False
            
            cache_key = self._make_key(key)
            result = await self.redis_client.delete(cache_key)
            return result > 0
            
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            if not self.redis_client:
                return False
            
            cache_key = self._make_key(key)
            result = await self.redis_client.exists(cache_key)
            return result > 0
            
        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value or None if error
        """
        try:
            if not self.redis_client:
                return None
            
            cache_key = self._make_key(key)
            result = await self.redis_client.incrby(cache_key, amount)
            return result
            
        except Exception as e:
            logger.warning(f"Cache increment error for key {key}: {e}")
            return None
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary mapping keys to values (missing keys excluded)
        """
        try:
            if not self.redis_client or not keys:
                return {}
            
            cache_keys = [self._make_key(key) for key in keys]
            values = await self.redis_client.mget(cache_keys)
            
            result = {}
            for i, (key, data) in enumerate(zip(keys, values)):
                if data is not None:
                    try:
                        result[key] = self._deserialize_pydantic(data)
                    except:
                        result[key] = pickle.loads(data)
            
            return result
            
        except Exception as e:
            logger.warning(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(
        self, 
        mapping: dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set multiple values in cache.
        
        Args:
            mapping: Dictionary mapping keys to values
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client or not mapping:
                return True
            
            ttl = ttl or self.default_ttl
            pipe = self.redis_client.pipeline()
            
            for key, value in mapping.items():
                cache_key = self._make_key(key)
                
                # Serialize based on type
                if hasattr(value, 'dict'):  # Pydantic model
                    data = self._serialize_pydantic(value)
                else:
                    data = pickle.dumps(value)
                
                pipe.setex(cache_key, ttl, data)
            
            await pipe.execute()
            return True
            
        except Exception as e:
            logger.warning(f"Cache set_many error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.
        
        Args:
            pattern: Key pattern (supports wildcards)
            
        Returns:
            Number of keys deleted
        """
        try:
            if not self.redis_client:
                return 0
            
            pattern_key = self._make_key(pattern)
            keys = await self.redis_client.keys(pattern_key)
            
            if keys:
                result = await self.redis_client.delete(*keys)
                return result
            
            return 0
            
        except Exception as e:
            logger.warning(f"Cache clear_pattern error for pattern {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            if not self.redis_client:
                return {}
            
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0)
            }
            
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {}
    
    def _serialize_pydantic(self, obj: Any) -> bytes:
        """Serialize Pydantic model to JSON bytes"""
        if hasattr(obj, 'dict'):
            data = {
                "_type": obj.__class__.__name__,
                "_data": obj.dict()
            }
            return json.dumps(data).encode('utf-8')
        else:
            raise ValueError("Object is not a Pydantic model")
    
    def _deserialize_pydantic(self, data: bytes) -> Any:
        """Deserialize JSON bytes to Pydantic model"""
        json_data = json.loads(data.decode('utf-8'))
        
        if "_type" in json_data and "_data" in json_data:
            obj_type = json_data["_type"]
            obj_data = json_data["_data"]
            
            # Map type names to classes
            type_mapping = {
                "LearnerCompetency": LearnerCompetency,
                "BKTParameters": BKTParameters
            }
            
            if obj_type in type_mapping:
                return type_mapping[obj_type](**obj_data)
        
        raise ValueError("Invalid Pydantic object format")


class InMemoryCache:
    """
    Simple in-memory cache fallback for development/testing.
    Not recommended for production use with multiple processes.
    """
    
    def __init__(self, default_ttl: int = 300):
        self.cache: dict[str, tuple[Any, datetime]] = {}
        self.default_ttl = default_ttl
    
    async def initialize(self):
        """Initialize (no-op for in-memory cache)"""
        logger.info("In-memory cache initialized")
    
    async def close(self):
        """Close (no-op for in-memory cache)"""
        pass
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            value, expires_at = self.cache[key]
            if datetime.utcnow() < expires_at:
                return value
            else:
                del self.cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self.cache[key] = (value, expires_at)
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        return await self.get(key) is not None
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern (simple implementation)"""
        import fnmatch
        keys_to_delete = [k for k in self.cache.keys() if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_delete:
            del self.cache[key]
        return len(keys_to_delete)