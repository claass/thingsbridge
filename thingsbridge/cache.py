"""Resource caching system with TTL for Things 3 integration."""

import time
import threading
from typing import Any, Callable, Dict, Optional, TypeVar
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TTLCache:
    """Thread-safe Time-To-Live cache for expensive operations."""
    
    def __init__(self, default_ttl_seconds: int = 300):  # 5 minutes default
        """
        Initialize TTL cache.
        
        Args:
            default_ttl_seconds: Default time-to-live in seconds (300 = 5 minutes)
        """
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str, factory_func: Callable[[], T], ttl_seconds: Optional[int] = None) -> T:
        """
        Get cached value or execute factory function if cache miss/expired.
        
        Args:
            key: Cache key
            factory_func: Function to call if cache miss/expired
            ttl_seconds: Override default TTL for this entry
            
        Returns:
            Cached or freshly computed value
        """
        ttl = ttl_seconds or self.default_ttl
        current_time = time.time()
        
        with self._lock:
            # Check if we have a valid cached entry
            if key in self._cache:
                entry = self._cache[key]
                if current_time - entry['timestamp'] < entry['ttl']:
                    logger.debug(f"Cache HIT for key '{key}'")
                    return entry['value']
                else:
                    logger.debug(f"Cache EXPIRED for key '{key}'")
            else:
                logger.debug(f"Cache MISS for key '{key}'")
        
        # Cache miss or expired - compute fresh value
        logger.debug(f"Executing factory function for key '{key}'")
        fresh_value = factory_func()
        
        # Store in cache
        with self._lock:
            self._cache[key] = {
                'value': fresh_value,
                'timestamp': current_time,
                'ttl': ttl
            }
        
        logger.debug(f"Cached fresh value for key '{key}' with TTL {ttl}s")
        return fresh_value
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if key was found and removed, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Invalidated cache key '{key}'")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            logger.debug("Cleared all cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            current_time = time.time()
            active_entries = 0
            expired_entries = 0
            
            for entry in self._cache.values():
                if current_time - entry['timestamp'] < entry['ttl']:
                    active_entries += 1
                else:
                    expired_entries += 1
            
            return {
                'total_entries': len(self._cache),
                'active_entries': active_entries,
                'expired_entries': expired_entries,
                'cache_keys': list(self._cache.keys())
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from cache. Returns number of entries removed."""
        current_time = time.time()
        removed_count = 0
        
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if current_time - entry['timestamp'] >= entry['ttl']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                removed_count += 1
            
            if removed_count > 0:
                logger.debug(f"Cleaned up {removed_count} expired cache entries")
        
        return removed_count


# Global cache instance for Things 3 resources
_resource_cache = TTLCache(default_ttl_seconds=300)  # 5 minutes


def get_resource_cache() -> TTLCache:
    """Get the global resource cache instance."""
    return _resource_cache


def cached_resource(cache_key: str, ttl_seconds: Optional[int] = None):
    """
    Decorator for caching expensive resource operations.
    
    Args:
        cache_key: Key to use for caching
        ttl_seconds: Optional TTL override
        
    Example:
        @cached_resource("areas_list", ttl_seconds=300)
        def areas_list():
            return expensive_areas_fetch()
    """
    def decorator(func: Callable[[], T]) -> Callable[[], T]:
        def wrapper() -> T:
            return _resource_cache.get(cache_key, func, ttl_seconds)
        return wrapper
    return decorator


def invalidate_resource_cache(cache_key: str) -> bool:
    """
    Invalidate a specific resource cache entry.
    
    Args:
        cache_key: Cache key to invalidate
        
    Returns:
        True if key was found and removed, False otherwise
    """
    return _resource_cache.invalidate(cache_key)


def clear_resource_cache() -> None:
    """Clear all resource cache entries."""
    _resource_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get resource cache statistics."""
    return _resource_cache.get_stats()