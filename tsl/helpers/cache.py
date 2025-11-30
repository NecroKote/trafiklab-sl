"""Cache protocol for helper utilities.

This module defines a cache interface using Python's Protocol type.
The library does not include cache implementations - clients can provide
their own cache that implements this protocol.

Example:
    Implementing a simple cache::

        from tsl.helpers import CacheProtocol

        class MyCache:
            def __init__(self):
                self._data = {}

            async def get(self, key: str):
                return self._data.get(key)

            async def set(self, key: str, value, ttl: int | None = None):
                self._data[key] = value

            async def delete(self, key: str):
                self._data.pop(key, None)

    Using with helpers::

        cache = MyCache()
        stops = StopHelper(session, cache=cache)
        lines = LineHelper(session, cache=cache)

    Home Assistant example::

        class HACache:
            def __init__(self, hass):
                self._data = hass.data.setdefault("tsl_cache", {})

            async def get(self, key: str):
                return self._data.get(key)

            async def set(self, key: str, value, ttl: int | None = None):
                self._data[key] = value

            async def delete(self, key: str):
                self._data.pop(key, None)
"""

from typing import Any, Protocol, runtime_checkable

__all__ = ("CacheProtocol",)


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol defining the cache interface for helper utilities.

    Implement this protocol to provide custom caching for StopHelper
    and LineHelper. The cache is optional - if not provided, helpers
    will fetch fresh data on each call.

    The protocol is marked as ``runtime_checkable``, allowing isinstance()
    checks if needed.

    Attributes:
        TTL_STATIC: Suggested TTL for static data like stops/lines (1 week).
            Implementations can use this as a hint for cache duration.

    Example:
        >>> class MyCache:
        ...     async def get(self, key: str) -> Any | None:
        ...         return self._storage.get(key)
        ...
        ...     async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ...         self._storage[key] = value
        ...
        ...     async def delete(self, key: str) -> None:
        ...         self._storage.pop(key, None)
        ...
        >>> cache = MyCache()
        >>> isinstance(cache, CacheProtocol)
        True
    """

    # Suggested TTL values (in seconds) - implementations can use these as hints
    TTL_STATIC: int = 604800  # 1 week - for stops/lines that rarely change

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Args:
            key: Cache key to look up.

        Returns:
            The cached value if found and not expired, None otherwise.
        """
        ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache (must be serializable if using persistent cache).
            ttl: Time-to-live in seconds. If None, use implementation default.
                Suggested: Use CacheProtocol.TTL_STATIC for stops/lines data.
        """
        ...

    async def delete(self, key: str) -> None:
        """Remove a value from the cache.

        Args:
            key: Cache key to delete.
        """
        ...
