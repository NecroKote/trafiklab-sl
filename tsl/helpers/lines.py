"""Line helper utilities with optional caching and search.

This module provides the LineHelper class for working with SL transit lines,
including filtering by transport mode and search functionality.

Note:
    This module depends on:
    - ``tsl.clients.transport`` (TransportClient with get_lines)
    - ``tsl.helpers.search`` (search algorithms)

Example:
    Basic usage without cache::

        async with aiohttp.ClientSession() as session:
            lines = LineHelper(session)
            metro = await lines.get_by_mode("metro")

    With custom cache::

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

# Default TTL for line data (1 week) - lines rarely change
DEFAULT_TTL = 604800


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

            cache = MyCache()  # Your CacheProtocol implementation
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
        """Initialize LineHelper.

        Args:
            session: aiohttp client session for API requests.
            cache: Optional cache implementing CacheProtocol.
            search_mode: Default search mode (SUBSTRING or FUZZY).
        """
        self._transport = TransportClient(session)
        self._cache = cache
        self._search_mode = search_mode
        self._preloaded = False

    @property
    def is_preloaded(self) -> bool:
        """Check if lines have been preloaded into cache.

        Returns:
            True if preload() has been called successfully.
        """
        return self._preloaded

    async def preload(self) -> None:
        """Eagerly load and cache all lines.

        Call this at application startup for faster response times.
        Requires a cache to be configured.

        Raises:
            RuntimeError: If no cache is configured.

        Example:
            >>> lines = LineHelper(session, cache=my_cache)
            >>> await lines.preload()
            >>> lines.is_preloaded
            True
        """
        if self._cache is None:
            raise RuntimeError("Cannot preload without a cache configured")
        await self.get_all()
        self._preloaded = True

    async def get_all(self) -> List[LineInfo]:
        """Get all lines as a flat list.

        Lines are sorted by transport_mode and then by designation.
        If a cache is configured, returns cached data when available.

        Returns:
            List of all LineInfo objects in the SL network.

        Example:
            >>> all_lines = await lines.get_all()
            >>> len(all_lines)
            523
        """
        # Try cache first
        if self._cache is not None:
            cached = await self._cache.get(self.CACHE_KEY)
            if cached is not None:
                return cached

        # Fetch from API
        lines = await self._fetch_all()

        # Store in cache if available
        if self._cache is not None:
            await self._cache.set(self.CACHE_KEY, lines, ttl=DEFAULT_TTL)

        return lines

    async def _fetch_all(self) -> List[LineInfo]:
        """Fetch all lines from Transport API.

        Returns:
            List of LineInfo objects from API response.
        """
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

        # Sort by mode then designation (natural sort for numbers)
        def sort_key(ln: LineInfo) -> tuple[str, str]:
            # Zero-pad numbers for natural sorting
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

        Example:
            >>> metro = await lines.get_by_mode("metro")
            >>> [ln.designation for ln in metro]
            ['10', '11', '13', '14', '17', '18', '19']
            >>> # Using enum
            >>> bus = await lines.get_by_mode(TransportMode.BUS)
        """
        # Convert enum to lowercase string to match API response keys
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

        Searches both the line designation (e.g., "176") and the line name
        (e.g., "Blå linjen"). Results are ranked by match quality.

        Args:
            query: Search query (e.g., "17", "blå", "grön").
            limit: Maximum number of results. Defaults to 10.
            mode: Search mode override. If None, uses instance default.

        Returns:
            List of matching LineInfo objects, sorted by relevance.

        Example:
            >>> results = await lines.search("blå")
            >>> [ln.name for ln in results if ln.name]
            ['Blå linjen']
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

        Example:
            >>> line = await lines.get_by_id(10)
            >>> line.name
            'Blå linjen'
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
            transport_mode: Optional filter by mode for disambiguation when
                multiple lines share the same designation.

        Returns:
            LineInfo if found, None otherwise.

        Example:
            >>> line = await lines.get_by_designation("17")
            >>> line.transport_mode
            'bus'
        """
        if transport_mode is not None:
            lines = await self.get_by_mode(transport_mode)
        else:
            lines = await self.get_all()

        return next((ln for ln in lines if ln.designation == designation), None)

    async def invalidate_cache(self) -> None:
        """Clear the lines cache.

        Call this if you need to force a refresh of line data.
        Has no effect if no cache is configured.

        Example:
            >>> await lines.invalidate_cache()
            >>> lines.is_preloaded
            False
        """
        if self._cache is not None:
            await self._cache.delete(self.CACHE_KEY)
        self._preloaded = False
