"""Line helper utilities with optional caching and search.

This module provides the LineHelper class for working with SL transit lines,
including filtering by transport mode and search functionality.
"""

from dataclasses import dataclass
from typing import List, Self

import aiohttp

from ..clients.transport import TransportClient
from ..models.common import TransportMode
from .cache import CacheProtocol
from .search import SearchMode, search

__all__ = (
    "LineInfo",
    "LineHelper",
)


@dataclass
class LineInfo:
    """Simplified line information for UI dropdowns"""

    id: int
    """Unique identifier of a line within a transport authority"""

    designation: str
    """
    Additional identifier for the line for example number for trains
    (e.g., "176", "17")
    """

    name: str | None
    """Line name generally known to the public (e.g., "Blå linjen")"""

    transport_mode: TransportMode
    """Transport mode for a line"""

    group_of_lines: str | None
    """Name used to group lines (e.g., "Blåbussar")"""

    def __str__(self) -> str:
        """Return human-readable representation."""
        transport_mode = self.transport_mode.value.lower()

        if self.name:
            return f"{self.designation} - {self.name} ({transport_mode})"

        return f"{self.designation} ({transport_mode})"


class LineHelper:
    """Helper for line operations with optional caching and search.

    Provides convenient access to SL transit lines with features for
    building user interfaces.

    **HINT**: If you plan on calling multiple methods, consider providing a cache
    implementation and using `preload()` since otherwise the underlying API
    returns ALL of its data for each call.

    Args:
        session: aiohttp client session for API requests.
        cache: Optional cache implementing CacheProtocol. If provided,
            line data will be cached for faster subsequent access.
        cache_ttl: Time-to-live for cached data in seconds. Defaults to 1 week.
        search_mode: Default search algorithm. SUBSTRING for exact matching,
            FUZZY for typo-tolerant search. Defaults to SUBSTRING.

    Example:
        ```python
        async with aiohttp.ClientSession() as session:
            lines = LineHelper(session)
            metro = await lines.get_by_mode(TransportMode.METRO)
        ```

        With custom cache:

        ```python
            cache = MyCache()  # Implements CacheProtocol
            lines = LineHelper(session, cache=cache).preload()
            metro = await lines.get_by_mode(TransportMode.METRO)
        ```
    """

    CACHE_KEY = "tsl:lines:all"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        cache: CacheProtocol | None = None,
        cache_ttl: int | None = 604800,  # 1 week
        search_mode: SearchMode = SearchMode.SUBSTRING,
    ) -> None:
        """Initialize LineHelper."""
        self._transport = TransportClient(session)
        self._cache = cache
        self._cache_ttl = cache_ttl
        self._search_mode = search_mode
        self._preloaded = False

    async def _fetch_all(self) -> List[LineInfo]:
        """Fetch all lines from Transport API."""
        result: List[LineInfo] = []

        lines_by_mode = await self._transport.get_lines()
        for mode, lines in lines_by_mode.items():
            for line in lines:
                _id = line["id"]
                result.append(
                    LineInfo(
                        id=_id,
                        designation=line.get("designation") or str(_id),
                        name=line.get("name"),
                        transport_mode=mode,
                        group_of_lines=line.get("group_of_lines"),
                    )
                )

        def sort_key(ln: LineInfo) -> tuple[str, str]:
            designation = ln.designation
            if designation.isdigit():
                designation = designation.zfill(5)
            return (ln.transport_mode, designation)

        return sorted(result, key=sort_key)

    @property
    def is_preloaded(self) -> bool:
        """Check if lines have been preloaded into cache."""
        return self._preloaded

    async def preload(self) -> Self:
        """Eagerly load and cache all lines.

        Raises:
            RuntimeError: If no cache is configured.
        """
        if self._cache is None:
            raise RuntimeError("Cannot preload without a cache configured")

        await self.get_all()
        self._preloaded = True

        return self

    async def invalidate_cache(self) -> Self:
        """Clear the lines cache."""

        if self._cache is not None:
            await self._cache.delete(self.CACHE_KEY)

        self._preloaded = False

        return self

    async def get_all(self) -> List[LineInfo]:
        """Get all lines as a flat list.

        Returns:
            List of all LineInfo objects in the SL network.
        """
        if self._cache is not None:
            cached = await self._cache.get(self.CACHE_KEY)
            if cached is not None:
                return cached

        lines = await self._fetch_all()

        if self._cache is not None:
            await self._cache.set(self.CACHE_KEY, lines, ttl=self._cache_ttl)

        return lines

    async def get_by_mode(self, mode: TransportMode) -> List[LineInfo]:
        """Get lines filtered by transport mode.

        Args:
            mode: Transport mode as string ("metro", "bus", "tram", "train",
                "ship", "ferry") or TransportMode enum.

        Returns:
            List of LineInfo objects for the specified mode.
        """
        all_lines = await self.get_all()
        return [ln for ln in all_lines if ln.transport_mode == mode]

    async def get_by_id(self, line_id: int) -> LineInfo | None:
        """Get line by ID.

        Args:
            line_id: Line ID from the API.

        Returns:
            LineInfo if found, None otherwise.

        Example:
            ```python
            line = await line_helper.get_by_id(17)
            print(line)
            # 17 (bus)
            metro = await line_helper.get_by_id(10)
            print(metro)
            # 10 - Blå linjen (metro)
            ```
        """
        all_lines = await self.get_all()
        return next((ln for ln in all_lines if ln.id == line_id), None)

    async def get_by_designation(
        self,
        designation: str,
        transport_mode: TransportMode | None = None,
    ) -> LineInfo | None:
        """Get line by designation (line number).

        Args:
            designation: Line designation (e.g., "17", "176").
            transport_mode: Optional filter by mode for disambiguation.

        Returns:
            LineInfo if found, None otherwise.
        """

        if transport_mode:
            lines = await self.get_by_mode(transport_mode)
        else:
            lines = await self.get_all()

        return next((ln for ln in lines if ln.designation == designation), None)

    async def search(
        self,
        query: str,
        limit: int = 10,
        mode: SearchMode | None = None,
    ) -> List[LineInfo]:
        """Search lines by designation or name.

        Args:
            query: Search query (e.g., "17", "blå", "grön").
            limit: Maximum number of results. Defaults to 10.
            mode: Search mode override.

        Returns:
            List of matching LineInfo objects.
        """

        if not query:
            return []

        all_lines = await self.get_all()
        return search(
            all_lines,
            query,
            key_fn=lambda ln: ln.designation + (f" {ln.name}" if ln.name else ""),
            mode=mode or self._search_mode,
            limit=limit,
        )
