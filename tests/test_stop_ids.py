"""Tests for stop_ids utility functions."""

import pytest

from tsl.tools.stop_ids import (
    global_id_to_site_id,
    global_id_to_stop_id,
    site_id_to_global_id,
    site_id_to_stop_id,
    stop_id_to_global_id,
    stop_id_to_site_id,
)


class TestSiteIdToGlobalId:
    """Tests for site_id_to_global_id conversion."""

    @pytest.mark.parametrize(
        "site_id,expected",
        [
            (9001, "9091001000009001"),  # T-Centralen
            (9117, "9091001000009117"),  # Odenplan
            (1002, "9091001000001002"),  # Centralen
            (102, "9091001000000102"),  # Small ID with padding
            (1, "9091001000000001"),  # Single digit
        ],
    )
    def test_conversion(self, site_id, expected):
        """Test various site_id to global_id conversions."""
        assert site_id_to_global_id(site_id) == expected

    def test_result_is_string(self):
        """Test that result is always a string."""
        result = site_id_to_global_id(9001)
        assert isinstance(result, str)

    def test_result_length(self):
        """Test that result is always 16 characters."""
        for site_id in [1, 99, 999, 9999]:
            result = site_id_to_global_id(site_id)
            assert len(result) == 16


class TestGlobalIdToSiteId:
    """Tests for global_id_to_site_id conversion."""

    @pytest.mark.parametrize(
        "global_id,expected",
        [
            ("9091001000009001", 9001),  # T-Centralen
            ("9091001000009117", 9117),  # Odenplan
            ("9091001000001002", 1002),  # Centralen
            ("9091001000000102", 102),  # Small ID
            ("9091001000000001", 1),  # Single digit
        ],
    )
    def test_conversion(self, global_id, expected):
        """Test various global_id to site_id conversions."""
        assert global_id_to_site_id(global_id) == expected

    def test_result_is_int(self):
        """Test that result is always an integer."""
        result = global_id_to_site_id("9091001000009001")
        assert isinstance(result, int)

    def test_invalid_prefix(self):
        """Test that invalid prefix raises ValueError."""
        with pytest.raises(ValueError, match="Invalid global ID format"):
            global_id_to_site_id("1234567890123456")

    def test_invalid_prefix_partial(self):
        """Test that partially matching prefix raises ValueError."""
        with pytest.raises(ValueError, match="Invalid global ID format"):
            global_id_to_site_id("9091001000109001")  # Wrong digit in middle


class TestSiteIdToStopId:
    """Tests for site_id_to_stop_id conversion."""

    @pytest.mark.parametrize(
        "site_id,expected",
        [
            (9001, "18009001"),  # T-Centralen
            (9117, "18009117"),  # Odenplan
            (1002, "18001002"),  # Centralen
            (102, "18000102"),  # Small ID with padding
        ],
    )
    def test_conversion(self, site_id, expected):
        """Test various site_id to stop_id conversions."""
        assert site_id_to_stop_id(site_id) == expected

    def test_result_is_string(self):
        """Test that result is always a string."""
        result = site_id_to_stop_id(9001)
        assert isinstance(result, str)

    def test_result_length(self):
        """Test that result is always 8 characters."""
        for site_id in [1, 99, 999, 9999]:
            result = site_id_to_stop_id(site_id)
            assert len(result) == 8


class TestStopIdToSiteId:
    """Tests for stop_id_to_site_id conversion."""

    @pytest.mark.parametrize(
        "stop_id,expected",
        [
            ("18009001", 9001),  # T-Centralen
            ("18009117", 9117),  # Odenplan
            ("18001002", 1002),  # Centralen
            ("18000102", 102),  # Small ID
        ],
    )
    def test_conversion(self, stop_id, expected):
        """Test various stop_id to site_id conversions."""
        assert stop_id_to_site_id(stop_id) == expected

    def test_result_is_int(self):
        """Test that result is always an integer."""
        result = stop_id_to_site_id("18009001")
        assert isinstance(result, int)

    def test_invalid_prefix(self):
        """Test that invalid prefix raises ValueError."""
        with pytest.raises(ValueError, match="Invalid stopId format"):
            stop_id_to_site_id("12349001")


class TestGlobalIdToStopId:
    """Tests for global_id_to_stop_id conversion."""

    @pytest.mark.parametrize(
        "global_id,expected",
        [
            ("9091001000009001", "18009001"),  # T-Centralen
            ("9091001000009117", "18009117"),  # Odenplan
        ],
    )
    def test_conversion(self, global_id, expected):
        """Test global_id to stop_id conversions."""
        assert global_id_to_stop_id(global_id) == expected


class TestStopIdToGlobalId:
    """Tests for stop_id_to_global_id conversion."""

    @pytest.mark.parametrize(
        "stop_id,expected",
        [
            ("18009001", "9091001000009001"),  # T-Centralen
            ("18009117", "9091001000009117"),  # Odenplan
        ],
    )
    def test_conversion(self, stop_id, expected):
        """Test stop_id to global_id conversions."""
        assert stop_id_to_global_id(stop_id) == expected


class TestRoundTrip:
    """Tests for round-trip conversions."""

    @pytest.mark.parametrize("site_id", [1, 102, 1002, 9001, 9117, 9999])
    def test_site_id_round_trip_via_global(self, site_id):
        """Test site_id -> global_id -> site_id round trip."""
        global_id = site_id_to_global_id(site_id)
        result = global_id_to_site_id(global_id)
        assert result == site_id

    @pytest.mark.parametrize("site_id", [1, 102, 1002, 9001, 9117, 9999])
    def test_site_id_round_trip_via_stop(self, site_id):
        """Test site_id -> stop_id -> site_id round trip."""
        stop_id = site_id_to_stop_id(site_id)
        result = stop_id_to_site_id(stop_id)
        assert result == site_id

    @pytest.mark.parametrize(
        "global_id",
        [
            "9091001000009001",
            "9091001000009117",
            "9091001000001002",
        ],
    )
    def test_global_id_round_trip(self, global_id):
        """Test global_id -> site_id -> global_id round trip."""
        site_id = global_id_to_site_id(global_id)
        result = site_id_to_global_id(site_id)
        assert result == global_id

    @pytest.mark.parametrize(
        "stop_id",
        [
            "18009001",
            "18009117",
            "18001002",
        ],
    )
    def test_stop_id_round_trip(self, stop_id):
        """Test stop_id -> site_id -> stop_id round trip."""
        site_id = stop_id_to_site_id(stop_id)
        result = site_id_to_stop_id(site_id)
        assert result == stop_id
