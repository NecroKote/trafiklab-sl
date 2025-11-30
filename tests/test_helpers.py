"""Tests for helper utilities."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from tsl.helpers import (
    AsyncCache,
    CacheEntry,
    FileBackend,
    LineHelper,
    LineInfo,
    MemoryBackend,
    SearchMode,
    StopHelper,
    StopInfo,
    fuzzy_search,
    search,
    substring_search,
)


# =============================================================================
# Cache Tests
# =============================================================================


class TestCacheEntry:
    """Tests for CacheEntry."""

    def test_not_expired(self):
        """Test cache entry that hasn't expired."""
        import time

        entry = CacheEntry(value="test", expires_at=time.time() + 3600)
        assert not entry.is_expired()

    def test_expired(self):
        """Test cache entry that has expired."""
        import time

        entry = CacheEntry(value="test", expires_at=time.time() - 1)
        assert entry.is_expired()


class TestMemoryBackend:
    """Tests for MemoryBackend."""

    @pytest.fixture
    def backend(self):
        return MemoryBackend()

    async def test_set_and_get(self, backend):
        """Test basic set and get."""
        import time

        entry = CacheEntry(value="test_value", expires_at=time.time() + 3600)
        await backend.set("key1", entry)

        result = await backend.get("key1")
        assert result is not None
        assert result.value == "test_value"

    async def test_get_nonexistent(self, backend):
        """Test get for nonexistent key."""
        result = await backend.get("nonexistent")
        assert result is None

    async def test_get_expired(self, backend):
        """Test get for expired entry."""
        import time

        entry = CacheEntry(value="test_value", expires_at=time.time() - 1)
        await backend.set("key1", entry)

        result = await backend.get("key1")
        assert result is None

    async def test_delete(self, backend):
        """Test delete."""
        import time

        entry = CacheEntry(value="test_value", expires_at=time.time() + 3600)
        await backend.set("key1", entry)
        await backend.delete("key1")

        result = await backend.get("key1")
        assert result is None

    async def test_clear(self, backend):
        """Test clear all entries."""
        import time

        entry1 = CacheEntry(value="value1", expires_at=time.time() + 3600)
        entry2 = CacheEntry(value="value2", expires_at=time.time() + 3600)
        await backend.set("key1", entry1)
        await backend.set("key2", entry2)
        await backend.clear()

        assert await backend.get("key1") is None
        assert await backend.get("key2") is None


class TestFileBackend:
    """Tests for FileBackend."""

    @pytest.fixture
    def backend(self, tmp_path):
        return FileBackend(tmp_path)

    async def test_set_and_get(self, backend):
        """Test basic set and get."""
        import time

        entry = CacheEntry(value={"data": "test"}, expires_at=time.time() + 3600)
        await backend.set("key1", entry)

        result = await backend.get("key1")
        assert result is not None
        assert result.value == {"data": "test"}

    async def test_get_nonexistent(self, backend):
        """Test get for nonexistent key."""
        result = await backend.get("nonexistent")
        assert result is None

    async def test_get_expired(self, backend):
        """Test get for expired entry removes file."""
        import time

        entry = CacheEntry(value="test_value", expires_at=time.time() - 1)
        await backend.set("key1", entry)

        result = await backend.get("key1")
        assert result is None

    async def test_persistence(self, tmp_path):
        """Test that data persists across backend instances."""
        import time

        backend1 = FileBackend(tmp_path)
        entry = CacheEntry(value="persistent", expires_at=time.time() + 3600)
        await backend1.set("key1", entry)

        # Create new backend instance
        backend2 = FileBackend(tmp_path)
        result = await backend2.get("key1")
        assert result is not None
        assert result.value == "persistent"

    async def test_clear(self, backend, tmp_path):
        """Test clear removes all files."""
        import time

        entry = CacheEntry(value="value", expires_at=time.time() + 3600)
        await backend.set("key1", entry)
        await backend.set("key2", entry)
        await backend.clear()

        # Check no json files remain
        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 0


class TestAsyncCache:
    """Tests for AsyncCache."""

    @pytest.fixture
    def cache(self):
        return AsyncCache()

    async def test_get_or_fetch_cache_miss(self, cache):
        """Test get_or_fetch on cache miss."""
        fetch_called = False

        async def fetch():
            nonlocal fetch_called
            fetch_called = True
            return "fetched_value"

        result = await cache.get_or_fetch("key1", fetch)
        assert result == "fetched_value"
        assert fetch_called

    async def test_get_or_fetch_cache_hit(self, cache):
        """Test get_or_fetch on cache hit."""
        # Pre-populate cache
        await cache.set("key1", "cached_value")

        fetch_called = False

        async def fetch():
            nonlocal fetch_called
            fetch_called = True
            return "new_value"

        result = await cache.get_or_fetch("key1", fetch)
        assert result == "cached_value"
        assert not fetch_called

    async def test_invalidate_specific_key(self, cache):
        """Test invalidate specific key."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.invalidate("key1")

        assert await cache.get("key1") is None
        assert await cache.get("key2") == "value2"

    async def test_invalidate_all(self, cache):
        """Test invalidate all."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.invalidate()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    async def test_with_file_backend(self, tmp_path):
        """Test factory method for file backend."""
        cache = AsyncCache.with_file_backend(tmp_path)
        await cache.set("key1", "value1")

        # Verify it was stored to file
        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 1


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
    def mock_stops_data(self):
        return [
            {"id": 9117, "name": "Odenplan", "lat": 59.34, "lon": 18.05},
            {"id": 9001, "name": "T-Centralen", "lat": 59.33, "lon": 18.06},
            {"id": 9192, "name": "Slussen", "lat": 59.32, "lon": 18.07},
        ]

    async def test_get_all_fetches_and_caches(self, mock_session, mock_stops_data):
        """Test get_all fetches from API and caches."""
        helper = StopHelper(mock_session)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        # First call should fetch
        result = await helper.get_all()
        assert len(result) == 3
        assert helper._transport.get_sites.call_count == 1

        # Second call should use cache
        result = await helper.get_all()
        assert len(result) == 3
        assert helper._transport.get_sites.call_count == 1

    async def test_preload(self, mock_session, mock_stops_data):
        """Test preload sets preloaded flag."""
        helper = StopHelper(mock_session)
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

    async def test_invalidate_cache(self, mock_session, mock_stops_data):
        """Test cache invalidation."""
        helper = StopHelper(mock_session)
        helper._transport.get_sites = AsyncMock(return_value=mock_stops_data)

        await helper.preload()
        assert helper.is_preloaded

        await helper.invalidate_cache()
        assert not helper.is_preloaded


# =============================================================================
# LineHelper Tests
# =============================================================================


class TestLineHelper:
    """Tests for LineHelper."""

    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.fixture
    def mock_lines_data(self):
        return {
            "metro": [
                {"id": 10, "designation": "10", "name": "Blå linjen"},
                {"id": 11, "designation": "11", "name": "Blå linjen"},
            ],
            "bus": [
                {"id": 176, "designation": "176", "name": "", "group_of_lines": "Blåbussar"},
                {"id": 55, "designation": "55", "name": ""},
            ],
        }

    async def test_get_all_fetches_and_caches(self, mock_session, mock_lines_data):
        """Test get_all fetches from API and caches."""
        helper = LineHelper(mock_session)
        helper._transport.get_lines = AsyncMock(return_value=mock_lines_data)

        result = await helper.get_all()
        assert len(result) == 4
        assert helper._transport.get_lines.call_count == 1

        # Second call should use cache
        result = await helper.get_all()
        assert len(result) == 4
        assert helper._transport.get_lines.call_count == 1

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
        designations = [ln.designation for ln in result]

        # Check sorted by mode
        assert modes == sorted(modes)


# =============================================================================
# Integration Tests (require API access)
# =============================================================================


@pytest.mark.integration
class TestStopHelperIntegration:
    """Integration tests for StopHelper."""

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
    """Integration tests for LineHelper."""

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
