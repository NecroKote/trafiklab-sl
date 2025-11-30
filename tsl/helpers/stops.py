"""Stop/site helper utilities with optional caching and search.

This module provides the StopHelper class for working with SL stops,
including search functionality and optional caching support.

Note:
    This module depends on:
    - ``tsl.clients.transport`` (TransportClient with get_sites)
    - ``tsl.clients.journey`` (JourneyPlannerClient with find_stops)
    - ``tsl.tools.stop_ids`` (ID conversion utilities)
    - ``tsl.helpers.search`` (search algorithms)

Example:
    Basic usage without cache::

        async with aiohttp.ClientSession() as session:
            stops = StopHelper(session)
            results = await stops.search("odenplan")

    With custom cache::

        cache = MyCache()  # Implements CacheProtocol
        stops = StopHelper(session, cache=cache)
        await stops.preload()  # Cache all stops at startup
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

# Default TTL for stop data (1 week) - stops rarely change
DEFAULT_TTL = 604800


@dataclass
class StopInfo:
    """Simplified stop information for UI dropdowns.

    Contains both ID formats needed for different SL APIs.

    Attributes:
        id: Transport API site_id (e.g., 9117). Use for departures API.
        global_id: Journey Planner ID (e.g., "9091001000009117"). Use for
            trip planning with SearchLeg.
        name: Stop name (e.g., "Odenplan").
        lat: Latitude coordinate, if available.
        lon: Longitude coordinate, if available.

    Example:
        >>> stop = await stop_helper.get_by_id(9117)
        >>> print(stop)
        Odenplan (9117)
        >>> # Use for departures
        >>> departures = await transport.get_site_departures(stop.id)
        >>> # Use for journey planning
        >>> origin = SearchLeg(type="stop", value=stop.global_id)
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

    Provides convenient access to SL stops with features for building
    user interfaces like autocomplete dropdowns.

    Features:
        - Optional caching via CacheProtocol (bring your own cache)
        - Fast local search with substring or fuzzy matching
        - Live search using Journey Planner API
        - Preloading for faster UI response

    Args:
        session: aiohttp client session for API requests.
        cache: Optional cache implementing CacheProtocol. If provided,
            stop data will be cached for faster subsequent access.
        search_mode: Default search algorithm. SUBSTRING for exact matching,
            FUZZY for typo-tolerant search. Defaults to SUBSTRING.

    Example:
        Without cache (fetches fresh data each time)::

            async with aiohttp.ClientSession() as session:
                stops = StopHelper(session)
                results = await stops.search("oden")

        With cache::

            cache = MyCache()  # Your CacheProtocol implementation
            stops = StopHelper(session, cache=cache)
            await stops.preload()  # Load all stops into cache

        With fuzzy search::

            stops = StopHelper(session, search_mode=SearchMode.FUZZY)
            results = await stops.search("tcentralen")  # Finds "T-Centralen"
    """

    CACHE_KEY = "tsl:stops:all"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        cache: CacheProtocol | None = None,
        search_mode: SearchMode = SearchMode.SUBSTRING,
    ) -> None:
        """Initialize StopHelper.

        Args:
            session: aiohttp client session for API requests.
            cache: Optional cache implementing CacheProtocol.
            search_mode: Default search mode (SUBSTRING or FUZZY).
        """
        self._transport = TransportClient(session)
        self._journey = JourneyPlannerClient(session)
        self._cache = cache
        self._search_mode = search_mode
        self._preloaded = False

    @property
    def is_preloaded(self) -> bool:
        """Check if stops have been preloaded into cache.

        Returns:
            True if preload() has been called successfully.
        """
        return self._preloaded

    async def preload(self) -> None:
        """Eagerly load and cache all stops.

        Call this at application startup for faster search response times.
        Requires a cache to be configured.

        Raises:
            RuntimeError: If no cache is configured.

        Example:
            >>> stops = StopHelper(session, cache=my_cache)
            >>> await stops.preload()
            >>> stops.is_preloaded
            True
        """
        if self._cache is None:
            raise RuntimeError("Cannot preload without a cache configured")
        await self.get_all()
        self._preloaded = True

    async def get_all(self) -> List[StopInfo]:
        """Get all stops in the SL network.

        If a cache is configured and contains valid data, returns cached
        data. Otherwise fetches from the API and caches the result.

        Returns:
            List of all StopInfo objects in the SL network.

        Example:
            >>> all_stops = await stops.get_all()
            >>> len(all_stops)
            4523
        """
        # Try cache first
        if self._cache is not None:
            cached = await self._cache.get(self.CACHE_KEY)
            if cached is not None:
                return cached

        # Fetch from API
        stops = await self._fetch_all()

        # Store in cache if available
        if self._cache is not None:
            await self._cache.set(self.CACHE_KEY, stops, ttl=DEFAULT_TTL)

        return stops

    async def _fetch_all(self) -> List[StopInfo]:
        """Fetch all sites from Transport API.

        Returns:
            List of StopInfo objects from API response.
        """
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

        Uses the cached list of all stops for fast local search.
        Results are ranked by match quality (exact > starts with > contains).

        Args:
            query: Search query (e.g., "oden", "t-central").
            limit: Maximum number of results. Defaults to 10.
            mode: Search mode override. If None, uses instance default.

        Returns:
            List of matching StopInfo objects, sorted by relevance.

        Example:
            >>> results = await stops.search("oden")
            >>> [s.name for s in results]
            ['Odenplan', 'Odenvägen', ...]
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
            site_id: Transport API site ID (e.g., 9117 for Odenplan).

        Returns:
            StopInfo if found, None otherwise.

        Example:
            >>> stop = await stops.get_by_id(9117)
            >>> stop.name
            'Odenplan'
        """
        all_stops = await self.get_all()
        return next((s for s in all_stops if s.id == site_id), None)

    async def get_by_global_id(self, global_id: str) -> StopInfo | None:
        """Get stop by Journey Planner global_id.

        Args:
            global_id: Journey Planner ID (e.g., "9091001000009117").

        Returns:
            StopInfo if found, None otherwise.

        Example:
            >>> stop = await stops.get_by_global_id("9091001000009117")
            >>> stop.name
            'Odenplan'
        """
        try:
            site_id = global_id_to_site_id(global_id)
            return await self.get_by_id(site_id)
        except ValueError:
            return None

    async def search_live(self, query: str, limit: int = 10) -> List[StopInfo]:
        """Live search using Journey Planner API.

        Unlike search(), this queries the API directly instead of using
        the cached stop list. Useful for real-time autocomplete when
        users are typing, as it may return more up-to-date results.

        Args:
            query: Search query string.
            limit: Maximum number of results. Defaults to 10.

        Returns:
            List of matching StopInfo objects from the API.

        Note:
            This method always makes an API call. For high-frequency
            autocomplete, consider using search() with cached data instead.

        Example:
            >>> results = await stops.search_live("t-cent")
            >>> results[0].name
            'T-Centralen'
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
                # Skip locations with unexpected ID format
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
        """Clear the stops cache.

        Call this if you need to force a refresh of stop data.
        Has no effect if no cache is configured.

        Example:
            >>> await stops.invalidate_cache()
            >>> stops.is_preloaded
            False
        """
        if self._cache is not None:
            await self._cache.delete(self.CACHE_KEY)
        self._preloaded = False
