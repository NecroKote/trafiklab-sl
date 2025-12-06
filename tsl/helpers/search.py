"""Search algorithms for helper utilities."""

from enum import Enum
from typing import Callable, List, TypeVar

__all__ = (
    "SearchMode",
    "substring_search",
    "fuzzy_search",
    "search",
)

T = TypeVar("T")


class SearchMode(Enum):
    """Available search modes."""

    SUBSTRING = "substring"  # Simple case-insensitive substring matching
    FUZZY = "fuzzy"  # Levenshtein-based fuzzy matching


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein (edit) distance between two strings.

    This is a simple dynamic programming implementation.
    """
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))

    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost is 0 if characters match, 1 otherwise
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _similarity_ratio(s1: str, s2: str) -> float:
    """Calculate similarity ratio (0-1) between two strings.

    Returns 1.0 for identical strings, 0.0 for completely different.
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    distance = _levenshtein_distance(s1.lower(), s2.lower())
    max_len = max(len(s1), len(s2))
    return 1.0 - (distance / max_len)


def substring_search(
    items: List[T],
    query: str,
    key_fn: Callable[[T], str],
    limit: int = 10,
) -> List[T]:
    """Fast substring search with ranking.

    Ranking priority:
    1. Exact match (case-insensitive)
    2. Starts with query
    3. Contains query

    Args:
        items: List of items to search
        query: Search query string
        key_fn: Function to extract searchable string from item
        limit: Maximum number of results

    Returns:
        List of matching items, sorted by relevance
    """
    if not query:
        return []

    query_lower = query.lower()
    exact: List[T] = []
    starts_with: List[T] = []
    contains: List[T] = []

    for item in items:
        text = key_fn(item).lower()

        if text == query_lower:
            exact.append(item)
        elif text.startswith(query_lower):
            starts_with.append(item)
        elif query_lower in text:
            contains.append(item)

    # Combine results in priority order
    results = exact + starts_with + contains
    return results[:limit]


def fuzzy_search(
    items: List[T],
    query: str,
    key_fn: Callable[[T], str],
    limit: int = 10,
    threshold: float = 0.6,
) -> List[T]:
    """Fuzzy search using Levenshtein distance.

    Handles typos like "tcentralen" -> "T-Centralen".

    Args:
        items: List of items to search
        query: Search query string
        key_fn: Function to extract searchable string from item
        limit: Maximum number of results
        threshold: Minimum similarity ratio (0-1) to include in results

    Returns:
        List of matching items, sorted by similarity
    """
    if not query:
        return []

    query_lower = query.lower()

    # Calculate similarity for all items
    scored: List[tuple[float, T]] = []

    for item in items:
        text = key_fn(item)
        text_lower = text.lower()

        # Check for substring match first (give it a bonus)
        if query_lower in text_lower:
            # Substring matches get a high score
            if text_lower == query_lower:
                score = 1.0  # Exact match
            elif text_lower.startswith(query_lower):
                score = 0.95  # Starts with
            else:
                score = 0.9  # Contains
        else:
            # Calculate fuzzy similarity
            # For long strings, compare against the most similar substring
            if len(text_lower) > len(query_lower) * 2:
                # Check similarity against words in the text
                words = text_lower.replace("-", " ").split()
                best_score = max(
                    (_similarity_ratio(query_lower, word) for word in words),
                    default=0.0,
                )
                # Also check full string similarity
                full_score = _similarity_ratio(query_lower, text_lower)
                score = max(best_score, full_score)
            else:
                score = _similarity_ratio(query_lower, text_lower)

        if score >= threshold:
            scored.append((score, item))

    # Sort by score (descending)
    scored.sort(key=lambda x: x[0], reverse=True)

    return [item for _, item in scored[:limit]]


def search(
    items: List[T],
    query: str,
    key_fn: Callable[[T], str],
    mode: SearchMode = SearchMode.SUBSTRING,
    limit: int = 10,
    **kwargs,
) -> List[T]:
    """Unified search function.

    Args:
        items: List of items to search
        query: Search query string
        key_fn: Function to extract searchable string from item
        mode: Search mode (SUBSTRING or FUZZY)
        limit: Maximum number of results
        **kwargs: Additional arguments passed to the search function
            - threshold: Minimum similarity for fuzzy search (default: 0.6)

    Returns:
        List of matching items
    """
    if mode == SearchMode.FUZZY:
        threshold = kwargs.get("threshold", 0.6)
        return fuzzy_search(items, query, key_fn, limit=limit, threshold=threshold)
    else:
        return substring_search(items, query, key_fn, limit=limit)
