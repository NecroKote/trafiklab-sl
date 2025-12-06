"""Tests for StopHelper.

Note: These tests require the following branches to be merged first:
- feature/transport-api-endpoints (for get_sites)
- feature/journey-extended-params (for find_stops)
- feature/stop-id-utilities (for ID conversions)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tsl.helpers import StopHelper, StopInfo


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

        result = await helper.get_all()
        assert len(result) == 3
        assert helper._transport.get_sites.call_count == 1

        result = await helper.get_all()
        assert len(result) == 3
        assert helper._transport.get_sites.call_count == 2

    async def test_get_all_with_cache(self, mock_session, mock_cache, mock_stops_data):
        """Test get_all uses cache when provided."""
        helper = StopHelper(mock_session, cache=mock_cache)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        result = await helper.get_all()
        assert len(result) == 3
        assert helper._transport.get_sites.call_count == 1

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

        await helper.invalidate_cache()


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
