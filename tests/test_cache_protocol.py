"""Tests for CacheProtocol."""

import pytest

from tsl.helpers import TTL_STATIC, CacheProtocol


class MockCache:
    """Mock cache implementation for testing."""

    def __init__(self):
        self._data = {}

    async def get(self, key: str):
        return self._data.get(key)

    async def set(self, key: str, value, ttl: int | None = None):
        self._data[key] = value

    async def delete(self, key: str):
        self._data.pop(key, None)


class TestCacheProtocol:
    """Tests for CacheProtocol."""

    def test_protocol_isinstance_check(self):
        """Test that MockCache is recognized as CacheProtocol."""
        cache = MockCache()
        assert isinstance(cache, CacheProtocol)

    def test_protocol_missing_method(self):
        """Test that incomplete implementation is not CacheProtocol."""

        class IncompleteCache:
            async def get(self, key: str):
                pass

            # Missing set and delete

        cache = IncompleteCache()
        assert not isinstance(cache, CacheProtocol)

    def test_ttl_static_value(self):
        """Test TTL_STATIC is 1 week."""
        assert TTL_STATIC == 604800

    async def test_mock_cache_operations(self):
        """Test mock cache basic operations."""
        cache = MockCache()

        # Test get returns None for missing key
        assert await cache.get("missing") is None

        # Test set and get
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"

        # Test delete
        await cache.delete("key1")
        assert await cache.get("key1") is None

        # Test delete non-existent key doesn't raise
        await cache.delete("nonexistent")
