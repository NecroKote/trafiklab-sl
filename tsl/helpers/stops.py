"""Stop/site helper utilities with caching and search."""

from dataclasses import dataclass
from typing import List

import aiohttp

from ..clients.journey import JourneyPlannerClient
from ..clients.transport import TransportClient
from ..tools.stop_ids import global_id_to_site_id, site_id_to_global_id
from .cache import AsyncCache
from .search import SearchMode, search

__all__ = (
    "StopInfo",
    "StopHelper",
)


@dataclass
class StopInfo:
    """Simplified stop information for UI dropdowns.

    Contains both ID formats needed for different SL APIs:
    - id: Transport API site_id (use for departures)
    - global_id: Journey Planner ID (use for trip planning)

    Example:
        stop = await stop_helper.get_by_id(9117)
        print(stop)  # "Odenplan (9117)"

        # Use for departures
        departures = await transport.get_site_departures(stop.id)

        # Use for journey planning
        origin = SearchLeg(type="stop", value=stop.global_id)
    """

    id: int  # Transport API site_id (e.g., 9117)
    global_id: str  # Journey Planner ID (e.g., "9091001000009117")
    name: str  # Stop name (e.g., "Odenplan")
    lat: float | None = None
    lon: float | None = None

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"


class StopHelper:
    """Helper for stop/site operations with caching and search.

    Provides:
    - Cached access to all stops in the SL network
    - Fast local search with substring or fuzzy matching
    - Live search using Journey Planner API
    - Preloading for faster UI response

    Example:
        async with aiohttp.ClientSession() as session:
            stops = StopHelper(session)

            # Search for stops
            results = await stops.search("oden")
            # [StopInfo(id=9117, name="Odenplan", ...), ...]

            # Get by ID
            stop = await stops.get_by_id(9117)

            # Live search (real-time autocomplete)
            results = await stops.search_live("t-cent")
    """

    CACHE_KEY = "stops:all"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        cache: AsyncCache | None = None,
        search_mode: SearchMode = SearchMode.SUBSTRING,
    ) -> None:
        """Initialize StopHelper.

        Args:
            session: aiohttp client session
            cache: AsyncCache instance (default: new MemoryBackend cache)
            search_mode: Default search mode (SUBSTRING or FUZZY)
        """
        self._transport = TransportClient(session)
        self._journey = JourneyPlannerClient(session)
        self._cache = cache or AsyncCache()
        self._search_mode = search_mode
        self._preloaded = False

    @property
    def is_preloaded(self) -> bool:
        """Check if stops have been preloaded."""
        return self._preloaded

    async def preload(self) -> None:
        """Eagerly load and cache all stops.

        Call this at startup for faster search response times.
        """
        await self.get_all()
        self._preloaded = True

    async def get_all(self) -> List[StopInfo]:
        """Get all stops in the SL network (cached).

        Returns:
            List of all StopInfo objects
        """
        return await self._cache.get_or_fetch(
            self.CACHE_KEY,
            self._fetch_all,
            ttl=AsyncCache.TTL_STATIC,
        )

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

        Uses the cached list of all stops for fast local search.

        Args:
            query: Search query (e.g., "oden", "t-central")
            limit: Maximum number of results (default: 10)
            mode: Search mode (default: instance default)

        Returns:
            List of matching StopInfo objects
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
            site_id: Transport API site ID (e.g., 9117)

        Returns:
            StopInfo if found, None otherwise
        """
        all_stops = await self.get_all()
        return next((s for s in all_stops if s.id == site_id), None)

    async def get_by_global_id(self, global_id: str) -> StopInfo | None:
        """Get stop by Journey Planner global_id.

        Args:
            global_id: Journey Planner ID (e.g., "9091001000009117")

        Returns:
            StopInfo if found, None otherwise
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
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching StopInfo objects
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
        """
        await self._cache.invalidate(self.CACHE_KEY)
        self._preloaded = False
