"""Search algorithms for helper utilities.

Note: This is a minimal stub. The full implementation is in
feature/helpers-search branch.
"""

from enum import Enum
from typing import Callable, List, TypeVar

__all__ = ("SearchMode", "search")

T = TypeVar("T")


class SearchMode(Enum):
    """Available search modes."""

    SUBSTRING = "substring"
    FUZZY = "fuzzy"


def search(
    items: List[T],
    query: str,
    key_fn: Callable[[T], str],
    mode: SearchMode = SearchMode.SUBSTRING,
    limit: int = 10,
    **kwargs,
) -> List[T]:
    """Search items by query. Uses substring matching by default."""
    if not query:
        return []

    query_lower = query.lower()
    matches = [item for item in items if query_lower in key_fn(item).lower()]
    return matches[:limit]
