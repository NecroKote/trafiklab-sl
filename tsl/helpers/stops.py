"""Stop/site helper utilities with optional caching and search.

This module provides the StopHelper class for working with SL stops.

Note:
    This module depends on:
    - ``tsl.clients.transport`` (TransportClient with get_sites)
    - ``tsl.clients.journey`` (JourneyPlannerClient with find_stops)
    - ``tsl.tools.stop_ids`` (ID conversion utilities)

Example:
    Basic usage without cache::

        async with aiohttp.ClientSession() as session:
            stops = StopHelper(session)
            results = await stops.search("odenplan")

    With custom cache::

        cache = MyCache()  # Implements CacheProtocol
        stops = StopHelper(session, cache=cache)
        await stops.preload()
"""

from dataclasses import dataclass
from typing import List

import aiohttp

from ..clients.journey import JourneyPlannerClient
from ..clients.transport import TransportClient
from ..tools.stop_ids import global_id_to_site_id, site_id_to_global_id
from .cache import CacheProtocol
from .search import SearchMode, search

__all__ = (
    "StopInfo",
    "StopHelper",
)

DEFAULT_TTL = 604800  # 1 week


@dataclass
class StopInfo:
    """Simplified stop information for UI dropdowns.

    Attributes:
        id: Transport API site_id (e.g., 9117). Use for departures API.
        global_id: Journey Planner ID (e.g., "9091001000009117").
        name: Stop name (e.g., "Odenplan").
        lat: Latitude coordinate, if available.
        lon: Longitude coordinate, if available.

    Example:
        >>> stop = await stop_helper.get_by_id(9117)
        >>> print(stop)
        Odenplan (9117)
    """

    id: int
    global_id: str
    name: str
    lat: float | None = None
    lon: float | None = None

    def __str__(self) -> str:
        """Return human-readable representation."""
        return f"{self.name} ({self.id})"


class StopHelper:
    """Helper for stop/site operations with optional caching and search.

    Features:
        - Optional caching via CacheProtocol (bring your own cache)
        - Fast local search with substring or fuzzy matching
        - Live search using Journey Planner API
        - Preloading for faster UI response

    Args:
        session: aiohttp client session for API requests.
        cache: Optional cache implementing CacheProtocol.
        search_mode: Default search algorithm. Defaults to SUBSTRING.

    Example:
        Without cache (fetches fresh data each time)::

            async with aiohttp.ClientSession() as session:
                stops = StopHelper(session)
                results = await stops.search("oden")

        With cache::

            cache = MyCache()  # Your CacheProtocol implementation
            stops = StopHelper(session, cache=cache)
            await stops.preload()
    """

    CACHE_KEY = "tsl:stops:all"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        cache: CacheProtocol | None = None,
        search_mode: SearchMode = SearchMode.SUBSTRING,
    ) -> None:
        """Initialize StopHelper."""
        self._transport = TransportClient(session)
        self._journey = JourneyPlannerClient(session)
        self._cache = cache
        self._search_mode = search_mode
        self._preloaded = False

    @property
    def is_preloaded(self) -> bool:
        """Check if stops have been preloaded into cache."""
        return self._preloaded

    async def preload(self) -> None:
        """Eagerly load and cache all stops.

        Raises:
            RuntimeError: If no cache is configured.
        """
        if self._cache is None:
            raise RuntimeError("Cannot preload without a cache configured")
        await self.get_all()
        self._preloaded = True

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
            await self._cache.set(self.CACHE_KEY, stops, ttl=DEFAULT_TTL)

        return stops

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
        try:
            site_id = global_id_to_site_id(global_id)
            return await self.get_by_id(site_id)
        except ValueError:
            return None

    async def search_live(self, query: str, limit: int = 10) -> List[StopInfo]:
        """Live search using Journey Planner API.

        Unlike search(), this queries the API directly.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of matching StopInfo objects from the API.
        """
        if not query:
            return []

        results = await self._journey.find_stops(query)
        stops: List[StopInfo] = []

        for loc in results[:limit]:
            global_id = loc.get("id", "")
            try:
                site_id = global_id_to_site_id(global_id)
            except ValueError:
                continue

            coord = loc.get("coord", [])
            lat = coord[0] if len(coord) > 0 else None
            lon = coord[1] if len(coord) > 1 else None

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

    async def invalidate_cache(self) -> None:
        """Clear the stops cache."""
        if self._cache is not None:
            await self._cache.delete(self.CACHE_KEY)
        self._preloaded = False
