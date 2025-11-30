"""Line helper utilities with caching and search."""

from dataclasses import dataclass
from typing import List

import aiohttp

from ..clients.transport import TransportClient
from ..models.common import TransportMode
from .cache import AsyncCache
from .search import SearchMode, search

__all__ = (
    "LineInfo",
    "LineHelper",
)


@dataclass
class LineInfo:
    """Simplified line information for UI dropdowns.

    Example:
        line = await line_helper.get_by_id(17)
        print(line)  # "17 (bus)"

        # For metro with name
        metro = await line_helper.get_by_id(10)
        print(metro)  # "10 - Blå linjen (metro)"
    """

    id: int  # Line ID
    designation: str  # Line number/code (e.g., "176", "17")
    name: str  # Line name (e.g., "Blå linjen", "" if none)
    transport_mode: str  # lowercase: "metro", "bus", "tram", etc.
    group_of_lines: str | None  # e.g., "Blåbussar", None if none

    def __str__(self) -> str:
        if self.name:
            return f"{self.designation} - {self.name} ({self.transport_mode})"
        return f"{self.designation} ({self.transport_mode})"


class LineHelper:
    """Helper for line operations with caching and search.

    Provides:
    - Cached access to all lines in the SL network
    - Filtering by transport mode
    - Fast local search with substring or fuzzy matching
    - Preloading for faster UI response

    Example:
        async with aiohttp.ClientSession() as session:
            lines = LineHelper(session)

            # Get all lines
            all_lines = await lines.get_all()

            # Get metro lines only
            metro = await lines.get_by_mode("metro")
            # Or using enum
            metro = await lines.get_by_mode(TransportMode.METRO)

            # Search for lines
            results = await lines.search("blå")
            # [LineInfo(designation="10", name="Blå linjen", ...), ...]
    """

    CACHE_KEY = "lines:all"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        cache: AsyncCache | None = None,
        search_mode: SearchMode = SearchMode.SUBSTRING,
    ) -> None:
        """Initialize LineHelper.

        Args:
            session: aiohttp client session
            cache: AsyncCache instance (default: new MemoryBackend cache)
            search_mode: Default search mode (SUBSTRING or FUZZY)
        """
        self._transport = TransportClient(session)
        self._cache = cache or AsyncCache()
        self._search_mode = search_mode
        self._preloaded = False

    @property
    def is_preloaded(self) -> bool:
        """Check if lines have been preloaded."""
        return self._preloaded

    async def preload(self) -> None:
        """Eagerly load and cache all lines.

        Call this at startup for faster search response times.
        """
        await self.get_all()
        self._preloaded = True

    async def get_all(self) -> List[LineInfo]:
        """Get all lines as a flat list (cached).

        Lines are sorted by transport_mode and then by designation.

        Returns:
            List of all LineInfo objects
        """
        return await self._cache.get_or_fetch(
            self.CACHE_KEY,
            self._fetch_all,
            ttl=AsyncCache.TTL_STATIC,
        )

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

        # Sort by mode then designation (natural sort for numbers)
        def sort_key(ln: LineInfo) -> tuple[str, str]:
            # Zero-pad numbers for natural sorting
            designation = ln.designation
            if designation.isdigit():
                designation = designation.zfill(5)
            return (ln.transport_mode, designation)

        return sorted(result, key=sort_key)

    async def get_by_mode(
        self, mode: str | TransportMode
    ) -> List[LineInfo]:
        """Get lines filtered by transport mode.

        Args:
            mode: Transport mode as string ("metro", "bus") or TransportMode enum

        Returns:
            List of LineInfo objects for the specified mode
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
        (e.g., "Blå linjen").

        Args:
            query: Search query (e.g., "17", "blå", "grön")
            limit: Maximum number of results (default: 10)
            mode: Search mode (default: instance default)

        Returns:
            List of matching LineInfo objects
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
            line_id: Line ID

        Returns:
            LineInfo if found, None otherwise
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
            designation: Line designation (e.g., "17", "176")
            transport_mode: Optional filter by mode (for disambiguation)

        Returns:
            LineInfo if found, None otherwise
        """
        if transport_mode is not None:
            lines = await self.get_by_mode(transport_mode)
        else:
            lines = await self.get_all()

        return next((ln for ln in lines if ln.designation == designation), None)

    async def invalidate_cache(self) -> None:
        """Clear the lines cache.

        Call this if you need to force a refresh of line data.
        """
        await self._cache.invalidate(self.CACHE_KEY)
        self._preloaded = False
