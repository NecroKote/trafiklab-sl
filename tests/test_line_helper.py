"""Tests for LineHelper.

Note: These tests require the following branches to be merged first:
- feature/transport-api-endpoints (for get_lines)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tsl.helpers import LineHelper, LineInfo


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

    def test_optional_group_of_lines(self):
        """Test optional group_of_lines."""
        line = LineInfo(
            id=10,
            designation="10",
            name="Blå linjen",
            transport_mode="metro",
            group_of_lines=None,
        )
        assert line.group_of_lines is None


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
                {"id": 11, "designation": "11", "name": "Gröna linjen"},
            ],
            "bus": [
                {
                    "id": 176,
                    "designation": "176",
                    "name": "",
                    "group_of_lines": "Blåbussar",
                },
                {"id": 1, "designation": "1", "name": ""},
            ],
        }

    async def test_get_all_without_cache(self, mock_session, mock_lines_data):
        """Test get_all fetches from API each time without cache."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_all()
        assert len(result) == 4
        assert helper._transport.get_lines.call_count == 1

        result = await helper.get_all()
        assert len(result) == 4
        assert helper._transport.get_lines.call_count == 2

    async def test_get_all_with_cache(self, mock_session, mock_cache, mock_lines_data):
        """Test get_all uses cache when provided."""
        helper = LineHelper(mock_session, cache=mock_cache)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_all()
        assert len(result) == 4
        assert helper._transport.get_lines.call_count == 1

        result = await helper.get_all()
        assert len(result) == 4
        assert helper._transport.get_lines.call_count == 1

    async def test_preload_requires_cache(self, mock_session, mock_lines_data):
        """Test preload raises error without cache."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        with pytest.raises(RuntimeError, match="Cannot preload without a cache"):
            await helper.preload()

    async def test_preload_with_cache(self, mock_session, mock_cache, mock_lines_data):
        """Test preload works with cache."""
        helper = LineHelper(mock_session, cache=mock_cache)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        assert not helper.is_preloaded
        await helper.preload()
        assert helper.is_preloaded

    async def test_get_by_mode(self, mock_session, mock_lines_data):
        """Test filtering by transport mode."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_by_mode("metro")
        assert len(result) == 2
        assert all(ln.transport_mode == "metro" for ln in result)

        result = await helper.get_by_mode("bus")
        assert len(result) == 2
        assert all(ln.transport_mode == "bus" for ln in result)

    async def test_search(self, mock_session, mock_lines_data):
        """Test search functionality."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.search("blå")
        assert len(result) == 1
        assert result[0].name == "Blå linjen"

    async def test_get_by_id(self, mock_session, mock_lines_data):
        """Test get_by_id."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_by_id(10)
        assert result is not None
        assert result.name == "Blå linjen"

        result = await helper.get_by_id(99999)
        assert result is None

    async def test_get_by_designation(self, mock_session, mock_lines_data):
        """Test get_by_designation."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_by_designation("176")
        assert result is not None
        assert result.transport_mode == "bus"

    async def test_invalidate_cache_with_cache(
        self, mock_session, mock_cache, mock_lines_data
    ):
        """Test cache invalidation with cache."""
        helper = LineHelper(mock_session, cache=mock_cache)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        await helper.preload()
        assert helper.is_preloaded

        await helper.invalidate_cache()
        assert not helper.is_preloaded

    async def test_invalidate_cache_without_cache(self, mock_session, mock_lines_data):
        """Test cache invalidation works without cache."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        await helper.invalidate_cache()

    async def test_sorting(self, mock_session, mock_lines_data):
        """Test lines are sorted by mode then designation."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_all()
        # Bus lines should be sorted naturally: 1, 176
        bus_lines = [ln for ln in result if ln.transport_mode == "bus"]
        assert bus_lines[0].designation == "1"
        assert bus_lines[1].designation == "176"


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

    async def test_search_blue_line(self, session):
        """Test searching for blue line."""
        helper = LineHelper(session)
        results = await helper.search("blå")

        assert len(results) > 0
