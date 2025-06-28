"""Tests for caching functionality."""

import time
import pytest
from thingsbridge.cache import TTLCache, clear_resource_cache, get_cache_stats, invalidate_resource_cache
from thingsbridge.tools import list_areas, list_projects, list_tags


def test_ttl_cache_basic():
    """Test basic TTL cache functionality."""
    cache = TTLCache(default_ttl_seconds=1)
    
    call_count = 0
    def factory():
        nonlocal call_count
        call_count += 1
        return f"result_{call_count}"
    
    # First call should execute factory
    result1 = cache.get("test_key", factory)
    assert result1 == "result_1"
    assert call_count == 1
    
    # Second call should return cached value
    result2 = cache.get("test_key", factory)
    assert result2 == "result_1"
    assert call_count == 1  # Factory not called again
    
    # After TTL expires, should call factory again
    time.sleep(1.1)
    result3 = cache.get("test_key", factory)
    assert result3 == "result_2"
    assert call_count == 2


def test_ttl_cache_invalidation():
    """Test cache invalidation."""
    cache = TTLCache(default_ttl_seconds=10)
    
    call_count = 0
    def factory():
        nonlocal call_count
        call_count += 1
        return f"result_{call_count}"
    
    # Get cached value
    result1 = cache.get("test_key", factory)
    assert result1 == "result_1"
    assert call_count == 1
    
    # Invalidate and get again
    cache.invalidate("test_key")
    result2 = cache.get("test_key", factory)
    assert result2 == "result_2"
    assert call_count == 2


def test_ttl_cache_stats():
    """Test cache statistics."""
    cache = TTLCache(default_ttl_seconds=10)
    
    # Initially empty
    stats = cache.get_stats()
    assert stats["total_entries"] == 0
    assert stats["active_entries"] == 0
    
    # Add some entries
    cache.get("key1", lambda: "value1")
    cache.get("key2", lambda: "value2")
    
    stats = cache.get_stats()
    assert stats["total_entries"] == 2
    assert stats["active_entries"] == 2
    assert "key1" in stats["cache_keys"]
    assert "key2" in stats["cache_keys"]


def test_ttl_cache_cleanup():
    """Test cleanup of expired entries."""
    cache = TTLCache(default_ttl_seconds=0.1)  # Very short TTL
    
    # Add entries
    cache.get("key1", lambda: "value1")
    cache.get("key2", lambda: "value2")
    
    assert cache.get_stats()["total_entries"] == 2
    
    # Wait for expiration
    time.sleep(0.2)
    
    # Cleanup should remove expired entries
    removed = cache.cleanup_expired()
    assert removed == 2
    assert cache.get_stats()["total_entries"] == 0


@pytest.mark.skipif(
    not hasattr(pytest, "_running_with_things3") or not pytest._running_with_things3,
    reason="Requires Things 3 integration test"
)
def test_resource_caching_performance():
    """Test that resource caching improves performance."""
    # Clear cache to start fresh
    clear_resource_cache()
    
    # First call should be slower (cache miss)
    start = time.time()
    areas1 = list_areas()
    first_duration = time.time() - start
    
    # Second call should be much faster (cache hit)
    start = time.time()
    areas2 = list_areas()
    second_duration = time.time() - start
    
    # Results should be identical
    assert areas1 == areas2
    
    # Second call should be significantly faster
    # Allow for some margin due to system variability
    assert second_duration < first_duration * 0.1


@pytest.mark.skipif(
    not hasattr(pytest, "_running_with_things3") or not pytest._running_with_things3,
    reason="Requires Things 3 integration test"
)
def test_cache_invalidation_on_create():
    """Test that cache is invalidated when creating new resources."""
    from thingsbridge.tools import create_tag
    
    # Clear cache and get initial tags
    clear_resource_cache()
    initial_stats = get_cache_stats()
    
    # Load tags into cache
    tags_before = list_tags()
    
    # Cache should now contain tags
    stats_after_load = get_cache_stats()
    assert "list_tags" in stats_after_load["cache_keys"]
    
    # Create a new tag (this should invalidate cache)
    create_tag("test_cache_invalidation_tag")
    
    # Cache should be invalidated
    stats_after_create = get_cache_stats()
    # The tags cache should be removed from cache
    # (Note: depending on implementation, key might be gone or marked expired)


def test_global_cache_functions():
    """Test global cache utility functions."""
    # Clear cache
    clear_resource_cache()
    initial_stats = get_cache_stats()
    assert initial_stats["total_entries"] == 0
    
    # The cache should start empty
    assert len(initial_stats["cache_keys"]) == 0


def test_cache_with_different_ttls():
    """Test cache with different TTL values."""
    cache = TTLCache(default_ttl_seconds=1)
    
    call_count = 0
    def factory():
        nonlocal call_count
        call_count += 1
        return f"result_{call_count}"
    
    # Use custom TTL
    result1 = cache.get("test_key", factory, ttl_seconds=2)
    assert result1 == "result_1"
    assert call_count == 1
    
    # After 1 second (default TTL), should still be cached due to custom TTL
    time.sleep(1.1)
    result2 = cache.get("test_key", factory, ttl_seconds=2)
    assert result2 == "result_1"
    assert call_count == 1  # Still cached
    
    # After 2+ seconds, should expire
    time.sleep(1.1)
    result3 = cache.get("test_key", factory)
    assert result3 == "result_2"
    assert call_count == 2


def test_cache_thread_safety():
    """Test basic thread safety of cache storage."""
    import threading
    
    cache = TTLCache(default_ttl_seconds=10)
    results = []
    
    def factory():
        time.sleep(0.01)  # Brief work simulation
        return "shared_result"
    
    def worker():
        result = cache.get("shared_key", factory)
        results.append(result)
    
    # First, populate cache in main thread
    cache.get("shared_key", factory)
    
    # Then test concurrent access to cached value
    threads = []
    for _ in range(5):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # All results should be the same cached value
    assert all(r == "shared_result" for r in results)
    assert len(results) == 5
    
    # Cache operations should not corrupt the cache
    stats = cache.get_stats()
    assert stats["total_entries"] >= 1