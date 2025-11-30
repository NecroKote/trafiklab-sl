"""Line helper utilities with optional caching and search.

This module provides the LineHelper class for working with SL transit lines,
including filtering by transport mode and search functionality.

Note:
    This module depends on:
    - ``tsl.clients.transport`` (TransportClient with get_lines)
    - ``tsl.models.common`` (TransportMode enum)

Example:
    Basic usage without cache::

        async with aiohttp.ClientSession() as session:
            lines = LineHelper(session)
            metro = await lines.get_by_mode("metro")

    With custom cache (e.g., Home Assistant)::

        cache = MyCache()  # Implements CacheProtocol
        lines = LineHelper(session, cache=cache)
        await lines.preload()  # Cache all lines at startup
"""

from dataclasses import dataclass
from typing import List

import aiohttp

from ..clients.transport import TransportClient
from ..models.common import TransportMode
from .cache import CacheProtocol
from .search import SearchMode, search

__all__ = (
    "LineInfo",
    "LineHelper",
)

DEFAULT_TTL = 604800  # 1 week


@dataclass
class LineInfo:
    """Simplified line information for UI dropdowns.

    Attributes:
        id: Line ID from the API.
        designation: Line number/code displayed to users (e.g., "176", "17").
        name: Line name if available (e.g., "Blå linjen"), empty string if none.
        transport_mode: Lowercase mode string ("metro", "bus", "tram", etc.).
        group_of_lines: Line group if available (e.g., "Blåbussar"), None if none.

    Example:
        >>> line = await line_helper.get_by_id(17)
        >>> print(line)
        17 (bus)
        >>> metro = await line_helper.get_by_id(10)
        >>> print(metro)
        10 - Blå linjen (metro)
    """

    id: int
    designation: str
    name: str
    transport_mode: str
    group_of_lines: str | None

    def __str__(self) -> str:
        """Return human-readable representation."""
        if self.name:
            return f"{self.designation} - {self.name} ({self.transport_mode})"
        return f"{self.designation} ({self.transport_mode})"


class LineHelper:
    """Helper for line operations with optional caching and search.

    Provides convenient access to SL transit lines with features for
    building user interfaces.

    Features:
        - Optional caching via CacheProtocol (bring your own cache)
        - Filtering by transport mode (metro, bus, tram, etc.)
        - Fast local search with substring or fuzzy matching
        - Preloading for faster UI response

    Args:
        session: aiohttp client session for API requests.
        cache: Optional cache implementing CacheProtocol. If provided,
            line data will be cached for faster subsequent access.
        search_mode: Default search algorithm. SUBSTRING for exact matching,
            FUZZY for typo-tolerant search. Defaults to SUBSTRING.

    Example:
        Without cache::

            async with aiohttp.ClientSession() as session:
                lines = LineHelper(session)
                all_lines = await lines.get_all()
                metro = await lines.get_by_mode("metro")

        With cache::

            cache = HACache(hass)  # Your CacheProtocol implementation
            lines = LineHelper(session, cache=cache)
            await lines.preload()

        Search for lines::

            results = await lines.search("blå")
            # [LineInfo(designation="10", name="Blå linjen", ...), ...]
    """

    CACHE_KEY = "tsl:lines:all"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        cache: CacheProtocol | None = None,
        search_mode: SearchMode = SearchMode.SUBSTRING,
    ) -> None:
        """Initialize LineHelper."""
        self._transport = TransportClient(session)
        self._cache = cache
        self._search_mode = search_mode
        self._preloaded = False

    @property
    def is_preloaded(self) -> bool:
        """Check if lines have been preloaded into cache."""
        return self._preloaded

    async def preload(self) -> None:
        """Eagerly load and cache all lines.

        Raises:
            RuntimeError: If no cache is configured.
        """
        if self._cache is None:
            raise RuntimeError("Cannot preload without a cache configured")
        await self.get_all()
        self._preloaded = True

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
            await self._cache.set(self.CACHE_KEY, lines, ttl=DEFAULT_TTL)

        return lines

    async def _fetch_all(self) -> List[LineInfo]:
        """Fetch all lines from Transport API."""
        lines_by_mode = await self._transport.get_lines()
        result: List[LineInfo] = []

        for mode, lines in lines_by_mode.items():
            for line in lines:
                result.append(
                    LineInfo(
                        id=line["id"],
                        designation=line.get("designation", str(line["id"])),
                        name=line.get("name", ""),
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

    async def get_by_mode(self, mode: str | TransportMode) -> List[LineInfo]:
        """Get lines filtered by transport mode.

        Args:
            mode: Transport mode as string ("metro", "bus", "tram", "train",
                "ship", "ferry") or TransportMode enum.

        Returns:
            List of LineInfo objects for the specified mode.
        """
        if isinstance(mode, TransportMode):
            mode_str = mode.value.lower()
        else:
            mode_str = mode.lower()

        all_lines = await self.get_all()
        return [ln for ln in all_lines if ln.transport_mode == mode_str]

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
            key_fn=lambda ln: f"{ln.designation} {ln.name}",
            mode=mode or self._search_mode,
            limit=limit,
        )

    async def get_by_id(self, line_id: int) -> LineInfo | None:
        """Get line by ID.

        Args:
            line_id: Line ID from the API.

        Returns:
            LineInfo if found, None otherwise.
        """
        all_lines = await self.get_all()
        return next((ln for ln in all_lines if ln.id == line_id), None)

    async def get_by_designation(
        self,
        designation: str,
        transport_mode: str | TransportMode | None = None,
    ) -> LineInfo | None:
        """Get line by designation (line number).

        Args:
            designation: Line designation (e.g., "17", "176").
            transport_mode: Optional filter by mode for disambiguation.

        Returns:
            LineInfo if found, None otherwise.
        """
        if transport_mode is not None:
            lines = await self.get_by_mode(transport_mode)
        else:
            lines = await self.get_all()

        return next((ln for ln in lines if ln.designation == designation), None)

    async def invalidate_cache(self) -> None:
        """Clear the lines cache."""
        if self._cache is not None:
            await self._cache.delete(self.CACHE_KEY)
        self._preloaded = False
