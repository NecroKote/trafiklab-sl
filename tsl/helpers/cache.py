"""Caching infrastructure for helper utilities."""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Generic, TypeVar
import asyncio
import hashlib
import json
import time

__all__ = (
    "CacheEntry",
    "CacheBackend",
    "MemoryBackend",
    "FileBackend",
    "AsyncCache",
)

T = TypeVar("T")


@dataclass
class CacheEntry:
    """A cached value with expiration time."""

    value: Any
    expires_at: float

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() > self.expires_at


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> CacheEntry | None:
        """Get a cache entry by key."""
        ...

    @abstractmethod
    async def set(self, key: str, entry: CacheEntry) -> None:
        """Store a cache entry."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a cache entry."""
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        ...


class MemoryBackend(CacheBackend):
    """In-memory cache backend (default).

    Data is stored in a dictionary and lost when the process exits.
    Thread-safe via asyncio.Lock.
    """

    def __init__(self) -> None:
        self._data: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> CacheEntry | None:
        """Get a cache entry by key."""
        async with self._lock:
            entry = self._data.get(key)
            if entry is not None and entry.is_expired():
                del self._data[key]
                return None
            return entry

    async def set(self, key: str, entry: CacheEntry) -> None:
        """Store a cache entry."""
        async with self._lock:
            self._data[key] = entry

    async def delete(self, key: str) -> None:
        """Delete a cache entry."""
        async with self._lock:
            self._data.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._data.clear()


class FileBackend(CacheBackend):
    """File-based persistent cache backend.

    Each cache entry is stored as a JSON file in the specified directory.
    Survives process restarts.
    """

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = Path(cache_dir)
        self._lock = asyncio.Lock()
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> Path:
        """Convert a cache key to a file path."""
        # Use hash to handle keys with special characters
        safe_key = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self._cache_dir / f"{safe_key}.json"

    async def get(self, key: str) -> CacheEntry | None:
        """Get a cache entry by key."""
        async with self._lock:
            path = self._key_to_path(key)
            if not path.exists():
                return None

            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                entry = CacheEntry(value=data["value"], expires_at=data["expires_at"])
                if entry.is_expired():
                    path.unlink(missing_ok=True)
                    return None
                return entry
            except (json.JSONDecodeError, KeyError, OSError):
                # Corrupted cache file, remove it
                path.unlink(missing_ok=True)
                return None

    async def set(self, key: str, entry: CacheEntry) -> None:
        """Store a cache entry."""
        async with self._lock:
            path = self._key_to_path(key)
            data = {"value": entry.value, "expires_at": entry.expires_at}
            path.write_text(json.dumps(data), encoding="utf-8")

    async def delete(self, key: str) -> None:
        """Delete a cache entry."""
        async with self._lock:
            path = self._key_to_path(key)
            path.unlink(missing_ok=True)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            for path in self._cache_dir.glob("*.json"):
                path.unlink(missing_ok=True)


class AsyncCache(Generic[T]):
    """Async cache with configurable backend and TTL.

    Example usage:
        cache = AsyncCache()  # In-memory, 24h TTL

        # With file backend
        cache = AsyncCache.with_file_backend(Path("~/.cache/tsl"))

        # Get or fetch pattern
        data = await cache.get_or_fetch("key", fetch_function, ttl=3600)
    """

    # Default TTLs in seconds
    TTL_STATIC = 86400  # 24 hours (sites, lines - rarely change)
    TTL_SEARCH = 3600  # 1 hour (search results)

    def __init__(
        self,
        backend: CacheBackend | None = None,
        default_ttl: int = TTL_STATIC,
    ) -> None:
        """Initialize the cache.

        Args:
            backend: Cache backend (default: MemoryBackend)
            default_ttl: Default TTL in seconds (default: 24 hours)
        """
        self._backend = backend or MemoryBackend()
        self._default_ttl = default_ttl
        self._fetch_locks: dict[str, asyncio.Lock] = {}

    async def get(self, key: str) -> T | None:
        """Get a value from the cache.

        Returns None if the key doesn't exist or has expired.
        """
        entry = await self._backend.get(key)
        if entry is None:
            return None
        return entry.value

    async def set(self, key: str, value: T, ttl: int | None = None) -> None:
        """Store a value in the cache.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time-to-live in seconds (default: default_ttl)
        """
        expires_at = time.time() + (ttl if ttl is not None else self._default_ttl)
        entry = CacheEntry(value=value, expires_at=expires_at)
        await self._backend.set(key, entry)

    async def get_or_fetch(
        self,
        key: str,
        fetch_fn: Callable[[], Awaitable[T]],
        ttl: int | None = None,
    ) -> T:
        """Get from cache or fetch and cache if missing.

        This method is safe for concurrent calls - only one fetch will
        be executed even if multiple callers request the same key.

        Args:
            key: Cache key
            fetch_fn: Async function to call if cache miss
            ttl: Time-to-live in seconds (default: default_ttl)

        Returns:
            Cached or freshly fetched value
        """
        # Check cache first (fast path)
        cached = await self.get(key)
        if cached is not None:
            return cached

        # Ensure only one fetch per key
        if key not in self._fetch_locks:
            self._fetch_locks[key] = asyncio.Lock()

        async with self._fetch_locks[key]:
            # Double-check after acquiring lock
            cached = await self.get(key)
            if cached is not None:
                return cached

            # Fetch and cache
            value = await fetch_fn()
            await self.set(key, value, ttl)
            return value

    async def invalidate(self, key: str | None = None) -> None:
        """Invalidate cache entries.

        Args:
            key: Specific key to invalidate, or None to clear all
        """
        if key is None:
            await self._backend.clear()
        else:
            await self._backend.delete(key)

    @classmethod
    def with_file_backend(
        cls,
        cache_dir: Path,
        default_ttl: int = TTL_STATIC,
    ) -> "AsyncCache[T]":
        """Factory method for file-based cache.

        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default TTL in seconds

        Returns:
            AsyncCache instance with FileBackend
        """
        return cls(backend=FileBackend(cache_dir), default_ttl=default_ttl)
