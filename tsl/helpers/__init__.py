"""Helper utilities for SL data.

This module provides LineHelper for working with SL transit lines.

Note:
    This module has dependencies on other PRs:
    - feature/helpers-cache-protocol (CacheProtocol)
    - feature/helpers-search (SearchMode, search)
    - feature/transport-api-endpoints (get_lines)

Example:
    Basic usage without cache::

        async with aiohttp.ClientSession() as session:
            lines = LineHelper(session)
            metro = await lines.get_by_mode("metro")

    With custom cache::

        cache = MyCache()  # Implements CacheProtocol
        lines = LineHelper(session, cache=cache)
        await lines.preload()
"""

from .cache import CacheProtocol
from .lines import LineHelper, LineInfo
from .search import SearchMode

__all__ = [
    "CacheProtocol",
    "LineHelper",
    "LineInfo",
    "SearchMode",
]
