"""Helper utilities for SL data with optional caching and search.

This module provides easy-to-use helpers for working with SL stops and lines,
including optional caching support and autocomplete search functionality.

Note:
    This module has dependencies on other modules:
    - StopHelper requires: transport client, journey client, stop_ids tools
    - LineHelper requires: transport client

Example:
    Basic usage without cache::

        import aiohttp
        from tsl.helpers import StopHelper, LineHelper

        async with aiohttp.ClientSession() as session:
            stops = StopHelper(session)
            lines = LineHelper(session)

            # Search for stops
            results = await stops.search("oden")
            # [StopInfo(id=9117, name="Odenplan", ...), ...]

            # Get all metro lines
            metro = await lines.get_by_mode("metro")

    With fuzzy search (handles typos)::

        from tsl.helpers import StopHelper, SearchMode

        stops = StopHelper(session, search_mode=SearchMode.FUZZY)
        results = await stops.search("tcentralen")  # Finds "T-Centralen"

    With custom cache (bring your own)::

        from tsl.helpers import CacheProtocol, StopHelper

        class MyCache:
            '''Your cache implementation.'''

            async def get(self, key: str):
                return self._storage.get(key)

            async def set(self, key: str, value, ttl: int | None = None):
                self._storage[key] = value

            async def delete(self, key: str):
                self._storage.pop(key, None)

        cache = MyCache()
        stops = StopHelper(session, cache=cache)
        await stops.preload()  # Load all stops into cache

    Home Assistant integration example::

        from homeassistant.helpers.aiohttp_client import async_get_clientsession
        from tsl.helpers import StopHelper, LineHelper, CacheProtocol

        class HACache:
            '''Home Assistant cache using hass.data.'''

            def __init__(self, hass):
                self._data = hass.data.setdefault("tsl_cache", {})

            async def get(self, key: str):
                return self._data.get(key)

            async def set(self, key: str, value, ttl: int | None = None):
                self._data[key] = value

            async def delete(self, key: str):
                self._data.pop(key, None)

        async def async_setup_entry(hass, entry):
            session = async_get_clientsession(hass)
            cache = HACache(hass)

            stop_helper = StopHelper(session, cache=cache)
            line_helper = LineHelper(session, cache=cache)

            # Preload for faster UI response
            await stop_helper.preload()
            await line_helper.preload()

            hass.data[DOMAIN] = {
                "stops": stop_helper,
                "lines": line_helper,
            }
"""

from .cache import CacheProtocol
from .lines import LineHelper, LineInfo
from .search import SearchMode, fuzzy_search, search, substring_search
from .stops import StopHelper, StopInfo

__all__ = [
    # Cache Protocol
    "CacheProtocol",
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
