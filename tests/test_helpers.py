"""Tests for helper utilities.

Note: These tests require the following branches to be merged first:
- feature/transport-api-endpoints (for get_lines, get_sites)
- feature/journey-extended-params (for find_stops)
- feature/stop-id-utilities (for ID conversions)
- feature/helpers-search (for search algorithms)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tsl.helpers import (
    CacheProtocol,
    LineHelper,
    LineInfo,
    SearchMode,
    StopHelper,
    StopInfo,
    fuzzy_search,
    search,
    substring_search,
)

# =============================================================================
# Mock Cache for Testing
# =============================================================================


class MockCache:
    """Mock cache implementation for testing."""

    def __init__(self):
        self._data = {}

    async def get(self, key: str):
        return self._data.get(key)

    async def set(self, key: str, value, ttl: int | None = None):
        self._data[key] = value

    async def delete(self, key: str):
        self._data.pop(key, None)


# =============================================================================
# CacheProtocol Tests
# =============================================================================


class TestCacheProtocol:
    """Tests for CacheProtocol."""

    def test_protocol_isinstance_check(self):
        """Test that MockCache is recognized as CacheProtocol."""
        cache = MockCache()
        assert isinstance(cache, CacheProtocol)

    def test_protocol_missing_method(self):
        """Test that incomplete implementation is not CacheProtocol."""

        class IncompleteCache:
            async def get(self, key: str):
                pass

            # Missing set and delete

        cache = IncompleteCache()
        assert not isinstance(cache, CacheProtocol)

    def test_ttl_static_value(self):
        """Test TTL_STATIC is 1 week."""
        assert CacheProtocol.TTL_STATIC == 604800


# =============================================================================
# Search Tests
# =============================================================================


class TestSubstringSearch:
    """Tests for substring_search."""

    def test_exact_match_first(self):
        """Test exact matches rank first."""
        items = ["Odenplan", "Odenplan T-bana", "Södra Odenplan"]
        result = substring_search(items, "odenplan", key_fn=lambda x: x)
        assert result[0] == "Odenplan"

    def test_starts_with_before_contains(self):
        """Test starts-with matches rank before contains."""
        items = ["Stockholm Odenplan", "Odenplan", "Odenplansgatan"]
        result = substring_search(items, "oden", key_fn=lambda x: x)
        # "Odenplan" and "Odenplansgatan" start with "oden", should come first
        assert result[0] in ["Odenplan", "Odenplansgatan"]
        assert result[-1] == "Stockholm Odenplan"

    def test_case_insensitive(self):
        """Test search is case insensitive."""
        items = ["T-Centralen", "Centralen", "Östermalmstorg"]
        result = substring_search(items, "CENTRALEN", key_fn=lambda x: x)
        assert len(result) == 2
        assert "T-Centralen" in result
        assert "Centralen" in result

    def test_empty_query(self):
        """Test empty query returns empty list."""
        items = ["A", "B", "C"]
        result = substring_search(items, "", key_fn=lambda x: x)
        assert result == []

    def test_no_matches(self):
        """Test no matches returns empty list."""
        items = ["A", "B", "C"]
        result = substring_search(items, "XYZ", key_fn=lambda x: x)
        assert result == []

    def test_limit(self):
        """Test limit parameter."""
        items = [f"Stop{i}" for i in range(20)]
        result = substring_search(items, "stop", key_fn=lambda x: x, limit=5)
        assert len(result) == 5


class TestFuzzySearch:
    """Tests for fuzzy_search."""

    def test_exact_match(self):
        """Test exact match gets highest score."""
        items = ["T-Centralen", "Centralen", "Other"]
        result = fuzzy_search(items, "T-Centralen", key_fn=lambda x: x)
        assert result[0] == "T-Centralen"

    def test_typo_correction(self):
        """Test fuzzy matching handles typos."""
        items = ["T-Centralen", "Odenplan", "Slussen"]
        result = fuzzy_search(items, "tcentralen", key_fn=lambda x: x, threshold=0.5)
        assert "T-Centralen" in result

    def test_threshold(self):
        """Test threshold filters out poor matches."""
        items = ["ABCDEF", "XYZ123"]
        # With high threshold, no matches
        result = fuzzy_search(items, "QQQ", key_fn=lambda x: x, threshold=0.9)
        assert len(result) == 0

    def test_empty_query(self):
        """Test empty query returns empty list."""
        items = ["A", "B", "C"]
        result = fuzzy_search(items, "", key_fn=lambda x: x)
        assert result == []


class TestUnifiedSearch:
    """Tests for unified search function."""

    def test_default_substring(self):
        """Test default mode is substring."""
        items = ["ABC", "ABCD", "XYZ"]
        result = search(items, "abc", key_fn=lambda x: x)
        assert len(result) == 2

    def test_fuzzy_mode(self):
        """Test fuzzy mode."""
        items = ["T-Centralen", "Odenplan"]
        result = search(
            items,
            "tcentralen",
            key_fn=lambda x: x,
            mode=SearchMode.FUZZY,
            threshold=0.5,
        )
        assert "T-Centralen" in result


# =============================================================================
# StopInfo Tests
# =============================================================================


class TestStopInfo:
    """Tests for StopInfo dataclass."""

    def test_str(self):
        """Test string representation."""
        stop = StopInfo(
            id=9117,
            global_id="9091001000009117",
            name="Odenplan",
            lat=59.34,
            lon=18.05,
        )
        assert str(stop) == "Odenplan (9117)"

    def test_optional_coordinates(self):
        """Test optional lat/lon."""
        stop = StopInfo(
            id=9117,
            global_id="9091001000009117",
            name="Odenplan",
        )
        assert stop.lat is None
        assert stop.lon is None


# =============================================================================
# LineInfo Tests
# =============================================================================


class TestLineInfo:
    """Tests for LineInfo dataclass."""

    def test_str_with_name(self):
        """Test string representation with name."""
        line = LineInfo(
            id=10,
            designation="10",
            name="Blå linjen",
            transport_mode="metro",
            group_of_lines=None,
        )
        assert str(line) == "10 - Blå linjen (metro)"

    def test_str_without_name(self):
        """Test string representation without name."""
        line = LineInfo(
            id=176,
            designation="176",
            name="",
            transport_mode="bus",
            group_of_lines="Blåbussar",
        )
        assert str(line) == "176 (bus)"


# =============================================================================
# StopHelper Tests
# =============================================================================


class TestStopHelper:
    """Tests for StopHelper."""

    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.fixture
    def mock_cache(self):
        return MockCache()

    @pytest.fixture
    def mock_stops_data(self):
        return [
            {"id": 9117, "name": "Odenplan", "lat": 59.34, "lon": 18.05},
            {"id": 9001, "name": "T-Centralen", "lat": 59.33, "lon": 18.06},
            {"id": 9192, "name": "Slussen", "lat": 59.32, "lon": 18.07},
        ]

    async def test_get_all_without_cache(self, mock_session, mock_stops_data):
        """Test get_all fetches from API each time without cache."""
        helper = StopHelper(mock_session)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        # First call should fetch
        result = await helper.get_all()
        assert len(result) == 3
        assert helper._transport.get_sites.call_count == 1

        # Second call should fetch again (no cache)
        result = await helper.get_all()
        assert len(result) == 3
        assert helper._transport.get_sites.call_count == 2

    async def test_get_all_with_cache(self, mock_session, mock_cache, mock_stops_data):
        """Test get_all uses cache when provided."""
        helper = StopHelper(mock_session, cache=mock_cache)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        # First call should fetch and cache
        result = await helper.get_all()
        assert len(result) == 3
        assert helper._transport.get_sites.call_count == 1

        # Second call should use cache
        result = await helper.get_all()
        assert len(result) == 3
        assert helper._transport.get_sites.call_count == 1

    async def test_preload_requires_cache(self, mock_session, mock_stops_data):
        """Test preload raises error without cache."""
        helper = StopHelper(mock_session)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        with pytest.raises(RuntimeError, match="Cannot preload without a cache"):
            await helper.preload()

    async def test_preload_with_cache(self, mock_session, mock_cache, mock_stops_data):
        """Test preload works with cache."""
        helper = StopHelper(mock_session, cache=mock_cache)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        assert not helper.is_preloaded
        await helper.preload()
        assert helper.is_preloaded

    async def test_search(self, mock_session, mock_stops_data):
        """Test search functionality."""
        helper = StopHelper(mock_session)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        result = await helper.search("oden")
        assert len(result) == 1
        assert result[0].name == "Odenplan"

    async def test_get_by_id(self, mock_session, mock_stops_data):
        """Test get_by_id."""
        helper = StopHelper(mock_session)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        result = await helper.get_by_id(9117)
        assert result is not None
        assert result.name == "Odenplan"

        result = await helper.get_by_id(99999)
        assert result is None

    async def test_get_by_global_id(self, mock_session, mock_stops_data):
        """Test get_by_global_id."""
        helper = StopHelper(mock_session)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        result = await helper.get_by_global_id("9091001000009117")
        assert result is not None
        assert result.name == "Odenplan"

    async def test_invalidate_cache_with_cache(
        self, mock_session, mock_cache, mock_stops_data
    ):
        """Test cache invalidation with cache."""
        helper = StopHelper(mock_session, cache=mock_cache)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        await helper.preload()
        assert helper.is_preloaded

        await helper.invalidate_cache()
        assert not helper.is_preloaded

    async def test_invalidate_cache_without_cache(self, mock_session, mock_stops_data):
        """Test cache invalidation works without cache."""
        helper = StopHelper(mock_session)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        # Should not raise
        await helper.invalidate_cache()


# =============================================================================
# LineHelper Tests
# =============================================================================


class TestLineHelper:
    """Tests for LineHelper."""

    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.fixture
    def mock_cache(self):
        return MockCache()

    @pytest.fixture
    def mock_lines_data(self):
        return {
            "metro": [
                {"id": 10, "designation": "10", "name": "Blå linjen"},
                {"id": 11, "designation": "11", "name": "Blå linjen"},
            ],
            "bus": [
                {
                    "id": 176,
                    "designation": "176",
                    "name": "",
                    "group_of_lines": "Blåbussar",
                },
                {"id": 55, "designation": "55", "name": ""},
            ],
        }

    async def test_get_all_without_cache(self, mock_session, mock_lines_data):
        """Test get_all fetches from API each time without cache."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_all()
        assert len(result) == 4
        assert helper._transport.get_lines.call_count == 1

        # Second call should fetch again (no cache)
        result = await helper.get_all()
        assert len(result) == 4
        assert helper._transport.get_lines.call_count == 2

    async def test_get_all_with_cache(self, mock_session, mock_cache, mock_lines_data):
        """Test get_all uses cache when provided."""
        helper = LineHelper(mock_session, cache=mock_cache)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        # First call should fetch and cache
        result = await helper.get_all()
        assert len(result) == 4
        assert helper._transport.get_lines.call_count == 1

        # Second call should use cache
        result = await helper.get_all()
        assert len(result) == 4
        assert helper._transport.get_lines.call_count == 1

    async def test_preload_requires_cache(self, mock_session, mock_lines_data):
        """Test preload raises error without cache."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        with pytest.raises(RuntimeError, match="Cannot preload without a cache"):
            await helper.preload()

    async def test_get_by_mode_string(self, mock_session, mock_lines_data):
        """Test get_by_mode with string."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_by_mode("metro")
        assert len(result) == 2
        assert all(ln.transport_mode == "metro" for ln in result)

    async def test_get_by_mode_enum(self, mock_session, mock_lines_data):
        """Test get_by_mode with TransportMode enum."""
        from tsl.models.common import TransportMode

        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_by_mode(TransportMode.BUS)
        assert len(result) == 2
        assert all(ln.transport_mode == "bus" for ln in result)

    async def test_search(self, mock_session, mock_lines_data):
        """Test search functionality."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.search("blå")
        assert len(result) >= 2  # Should find Blå linjen lines

    async def test_get_by_id(self, mock_session, mock_lines_data):
        """Test get_by_id."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_by_id(10)
        assert result is not None
        assert result.designation == "10"

        result = await helper.get_by_id(99999)
        assert result is None

    async def test_get_by_designation(self, mock_session, mock_lines_data):
        """Test get_by_designation."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_by_designation("176")
        assert result is not None
        assert result.id == 176

    async def test_get_by_designation_with_mode(self, mock_session, mock_lines_data):
        """Test get_by_designation with mode filter."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_by_designation("176", transport_mode="bus")
        assert result is not None
        assert result.transport_mode == "bus"

    async def test_sorting(self, mock_session, mock_lines_data):
        """Test lines are sorted by mode then designation."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_all()
        # Should be sorted: bus 55, bus 176, metro 10, metro 11
        modes = [ln.transport_mode for ln in result]

        # Check sorted by mode
        assert modes == sorted(modes)


# =============================================================================
# Integration Tests (require API access and all dependencies)
# =============================================================================


@pytest.mark.integration
class TestStopHelperIntegration:
    """Integration tests for StopHelper.

    Note: Requires feature/transport-api-endpoints, feature/journey-extended-params,
    and feature/stop-id-utilities to be merged.
    """

    @pytest.fixture
    async def session(self):
        import aiohttp

        async with aiohttp.ClientSession() as session:
            yield session

    async def test_get_all_stops(self, session):
        """Test fetching all stops from API."""
        helper = StopHelper(session)
        stops = await helper.get_all()

        assert len(stops) > 0
        assert all(isinstance(s, StopInfo) for s in stops)

    async def test_search_odenplan(self, session):
        """Test searching for Odenplan."""
        helper = StopHelper(session)
        results = await helper.search("odenplan")

        assert len(results) > 0
        assert any(s.name == "Odenplan" for s in results)

    async def test_search_live(self, session):
        """Test live search functionality."""
        helper = StopHelper(session)
        results = await helper.search_live("t-central")

        assert len(results) > 0


@pytest.mark.integration
class TestLineHelperIntegration:
    """Integration tests for LineHelper.

    Note: Requires feature/transport-api-endpoints to be merged.
    """

    @pytest.fixture
    async def session(self):
        import aiohttp

        async with aiohttp.ClientSession() as session:
            yield session

    async def test_get_all_lines(self, session):
        """Test fetching all lines from API."""
        helper = LineHelper(session)
        lines = await helper.get_all()

        assert len(lines) > 0
        assert all(isinstance(ln, LineInfo) for ln in lines)

    async def test_get_metro_lines(self, session):
        """Test fetching metro lines."""
        helper = LineHelper(session)
        metro = await helper.get_by_mode("metro")

        assert len(metro) > 0
        assert all(ln.transport_mode == "metro" for ln in metro)

    async def test_search_lines(self, session):
        """Test searching for lines."""
        helper = LineHelper(session)
        results = await helper.search("17")

        assert len(results) > 0
