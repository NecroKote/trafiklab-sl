"""Cache protocol for helper utilities.

This module defines a cache interface using Python's Protocol type.
The library does not include cache implementations - clients can provide
their own cache that implements this protocol.
"""

from typing import Any, Protocol, runtime_checkable

__all__ = ("CacheProtocol",)


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol defining the cache interface for helper utilities.

    Implement this protocol to provide custom caching for helpers.
    The cache is optional - if not provided, helpers will fetch
    fresh data on each call.

    Attributes:
        TTL_STATIC: Suggested TTL for static data like stops/lines (1 week).
    """

    TTL_STATIC: int = 604800  # 1 week

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache."""
        ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value in the cache."""
        ...

    async def delete(self, key: str) -> None:
        """Remove a value from the cache."""
        ...
