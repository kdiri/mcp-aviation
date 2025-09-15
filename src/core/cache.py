"""Caching system for performance optimization."""

import time
import logging
from typing import Any, Dict, Optional, Tuple
from functools import wraps
from threading import Lock

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        """Initialize cache with default TTL in seconds."""
        self.default_ttl = default_ttl
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if time.time() < expiry:
                    return value
                else:
                    # Remove expired entry
                    del self.cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        
        with self.lock:
            self.cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        with self.lock:
            return len(self.cache)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        current_time = time.time()
        expired_keys = []
        
        with self.lock:
            for key, (_, expiry) in self.cache.items():
                if current_time >= expiry:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)


# Global cache instances
aircraft_specs_cache = InMemoryCache(default_ttl=3600)  # 1 hour
geocoding_cache = InMemoryCache(default_ttl=1800)  # 30 minutes
airport_search_cache = InMemoryCache(default_ttl=300)  # 5 minutes


def cache_result(cache_instance: InMemoryCache, key_func=None, ttl=None):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            
            return result
        return wrapper
    return decorator


def geocoding_key_func(location: str) -> str:
    """Generate cache key for geocoding."""
    return f"geocode:{location.lower().strip()}"


def airport_search_key_func(location, aircraft_type, max_distance_nm) -> str:
    """Generate cache key for airport search."""
    location_str = str(location).lower().strip()
    return f"search:{location_str}:{aircraft_type}:{max_distance_nm}"