"""Helper utilities for SL data with caching and search.

This module provides easy-to-use helpers for working with SL stops and lines,
including caching and autocomplete search functionality.

Example usage:
    import aiohttp
    from tsl.helpers import StopHelper, LineHelper, AsyncCache

    async with aiohttp.ClientSession() as session:
        # Create helpers (shared cache)
        cache = AsyncCache()
        stops = StopHelper(session, cache)
        lines = LineHelper(session, cache)

        # Search for stops
        results = await stops.search("oden")
        # [StopInfo(id=9117, name="Odenplan", ...), ...]

        # Get all metro lines
        metro = await lines.get_by_mode("metro")
        # [LineInfo(id=10, designation="10", name="Blå linjen"), ...]

With fuzzy search (handles typos):
    from tsl.helpers import StopHelper, SearchMode

    stops = StopHelper(session, search_mode=SearchMode.FUZZY)
    results = await stops.search("tcentralen")  # Finds "T-Centralen"

With file-based persistent cache:
    from pathlib import Path
    from tsl.helpers import AsyncCache, StopHelper

    cache = AsyncCache.with_file_backend(Path("~/.tsl/cache").expanduser())
    stops = StopHelper(session, cache)

Home Assistant integration example:
    async def async_setup_entry(hass, entry):
        session = async_get_clientsession(hass)

        # Use HA's config directory for cache
        cache_dir = Path(hass.config.path("tsl_cache"))
        cache = AsyncCache.with_file_backend(cache_dir)

        # Create helpers
        stop_helper = StopHelper(session, cache)
        line_helper = LineHelper(session, cache)

        # Preload for faster UI response
        await stop_helper.preload()
        await line_helper.preload()

        hass.data[DOMAIN] = {
            "stops": stop_helper,
            "lines": line_helper,
        }
"""

from .cache import AsyncCache, CacheBackend, CacheEntry, FileBackend, MemoryBackend
from .lines import LineHelper, LineInfo
from .search import SearchMode, fuzzy_search, search, substring_search
from .stops import StopHelper, StopInfo

__all__ = [
    # Cache
    "AsyncCache",
    "CacheBackend",
    "CacheEntry",
    "MemoryBackend",
    "FileBackend",
    # Search
    "SearchMode",
    "search",
    "substring_search",
    "fuzzy_search",
    # Helpers
    "StopHelper",
    "StopInfo",
    "LineHelper",
    "LineInfo",
]
