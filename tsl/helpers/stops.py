"""Stop/site helper utilities with optional caching and search.

This module provides the StopHelper class for working with SL stops.
"""

from dataclasses import dataclass
from typing import List, Self

import aiohttp

from ..clients.journey import JourneyPlannerClient
from ..clients.transport import TransportClient
from ..models.journey import SearchLeg
from ..tools.stop_ids import global_id_to_site_id, site_id_to_global_id
from .cache import CacheProtocol
from .search import SearchMode, search

__all__ = (
    "StopInfo",
    "StopHelper",
)


@dataclass
class StopInfo:
    """Simplified stop information for UI dropdowns."""

    id: int
    """Transport API site_id (e.g., 9117). Use for departures API."""

    global_id: str
    """Journey Planner ID (e.g., "9091001000009117")."""

    name: str
    """Stop name (e.g., "Odenplan")."""

    lat: float | None = None
    """Latitude coordinate, if available."""

    lon: float | None = None
    """Longitude coordinate, if available."""

    def __str__(self) -> str:
        """Return human-readable representation."""
        return f"{self.name} ({self.id})"


class StopHelper:
    """Helper for stop/site operations with optional caching and search.

    Provides convenient access to SL stops with features for building user
    interfaces.

    **HINT**: If you plan on calling multiple methods, consider providing a cache
    implementation and using `preload()` since otherwise the underlying API
    returns ALL of its data for each call.

    Args:
        session: aiohttp client session for API requests.
        cache: Optional cache implementing CacheProtocol. If provided,
            stops data will be cached for faster subsequent access.
        cache_ttl: Time-to-live for cached data in seconds. Defaults to 1 week.
        search_mode: Default search algorithm. SUBSTRING for exact matching,
            FUZZY for typo-tolerant search. Defaults to SUBSTRING.

    Example:
        ```python
        async with aiohttp.ClientSession() as session:
            stops = StopHelper(session)
            results = await stops.search("oden")
        ```

        With custom cache:
        ```python
            cache = MyCache()  # Implements CacheProtocol
            stops = await StopHelper(session, cache=cache).preload()
            results = await stops.search("oden")
        ```
    """

    CACHE_KEY = "tsl:stops:all"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        cache: CacheProtocol | None = None,
        cache_ttl: int | None = 604800,  # 1 week
        search_mode: SearchMode = SearchMode.SUBSTRING,
    ) -> None:
        """Initialize StopHelper."""
        self._transport = TransportClient(session)
        self._journey = JourneyPlannerClient(session)
        self._cache = cache
        self._cache_ttl = cache_ttl
        self._search_mode = search_mode
        self._preloaded = False

    async def _fetch_all(self) -> List[StopInfo]:
        """Fetch all sites from Transport API."""
        sites = await self._transport.get_sites()
        return [
            StopInfo(
                id=site["id"],
                global_id=site_id_to_global_id(site["id"]),
                name=site["name"],
                lat=site.get("lat"),
                lon=site.get("lon"),
            )
            for site in sites
        ]

    @property
    def is_preloaded(self) -> bool:
        """Check if stops have been preloaded into cache."""
        return self._preloaded

    async def preload(self) -> Self:
        """Eagerly load and cache all stops.

        Raises:
            RuntimeError: If no cache is configured.
        """
        if self._cache is None:
            raise RuntimeError("Cannot preload without a cache configured")

        await self.get_all()
        self._preloaded = True

        return self

    async def invalidate_cache(self) -> Self:
        """Clear the stops cache."""

        if self._cache is not None:
            await self._cache.delete(self.CACHE_KEY)

        self._preloaded = False

        return self

    async def get_all(self) -> List[StopInfo]:
        """Get all stops in the SL network.

        Returns:
            List of all StopInfo objects.
        """
        if self._cache is not None:
            cached = await self._cache.get(self.CACHE_KEY)
            if cached is not None:
                return cached

        stops = await self._fetch_all()

        if self._cache is not None:
            await self._cache.set(self.CACHE_KEY, stops, ttl=self._cache_ttl)

        return stops

    async def get_by_id(self, site_id: int) -> StopInfo | None:
        """Get stop by Transport API site_id.

        Args:
            site_id: Transport API site ID (e.g., 9117).

        Returns:
            StopInfo if found, None otherwise.
        """
        all_stops = await self.get_all()
        return next((s for s in all_stops if s.id == site_id), None)

    async def get_by_global_id(self, global_id: str) -> StopInfo | None:
        """Get stop by Journey Planner global_id.

        Args:
            global_id: Journey Planner ID (e.g., "9091001000009117").

        Returns:
            StopInfo if found, None otherwise.
        """
        all_stops = await self.get_all()
        return next((s for s in all_stops if s.global_id == global_id), None)

    async def search(
        self,
        query: str,
        limit: int = 10,
        mode: SearchMode | None = None,
    ) -> List[StopInfo]:
        """Search stops by name.

        Args:
            query: Search query (e.g., "oden", "t-central").
            limit: Maximum number of results. Defaults to 10.
            mode: Search mode override.

        Returns:
            List of matching StopInfo objects.
        """
        if not query:
            return []

        all_stops = await self.get_all()
        return search(
            all_stops,
            query,
            key_fn=lambda s: s.name,
            mode=mode or self._search_mode,
            limit=limit,
        )

    async def search_live(self, query: str, limit: int = 10) -> List[StopInfo]:
        """Live search using Journey Planner API.

        Unlike search(), this method DOES NOT use cache and queries the API directly.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of matching StopInfo objects from the API.
        """
        if not query:
            return []

        results = await self._journey.find_stops(SearchLeg.from_any(query))
        stops: List[StopInfo] = []

        for loc in results[:limit]:
            global_id = loc["id"]
            site_id = global_id_to_site_id(global_id)
            lat, lon = loc["coord"]

            stops.append(
                StopInfo(
                    id=site_id,
                    global_id=global_id,
                    name=loc.get("disassembledName", loc.get("name", "")),
                    lat=lat,
                    lon=lon,
                )
            )

        return stops
