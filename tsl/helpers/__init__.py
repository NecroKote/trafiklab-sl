"""Helper utilities for SL data.

This module provides StopHelper for working with SL stops.

Note:
    This module has dependencies on other PRs:
    - feature/helpers-cache-protocol (CacheProtocol)
    - feature/helpers-search (SearchMode, search)
    - feature/transport-api-endpoints (get_sites)
    - feature/journey-extended-params (find_stops)
    - feature/stop-id-utilities (ID conversions)

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

from .cache import CacheProtocol, TTL_STATIC
from .search import SearchMode, search
from .stops import StopHelper, StopInfo

__all__ = (
    "CacheProtocol",
    "TTL_STATIC",
    "SearchMode",
    "search", 
    "StopHelper",
    "StopInfo",
)
