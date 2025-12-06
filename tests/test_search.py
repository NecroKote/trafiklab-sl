"""Tests for search utilities."""

import pytest

from tsl.helpers.search import (
    SearchMode,
    fuzzy_search,
    search,
    substring_search,
)


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

    def test_custom_key_fn(self):
        """Test with custom key function."""
        items = [{"name": "Odenplan"}, {"name": "T-Centralen"}, {"name": "Slussen"}]
        result = substring_search(items, "oden", key_fn=lambda x: x["name"])
        assert len(result) == 1
        assert result[0]["name"] == "Odenplan"


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

    def test_missing_hyphen(self):
        """Test fuzzy matching handles missing hyphen."""
        items = ["T-Centralen", "Odenplan", "Slussen"]
        result = fuzzy_search(items, "t centralen", key_fn=lambda x: x, threshold=0.5)
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

    def test_limit(self):
        """Test limit parameter."""
        items = [f"Stop{i}" for i in range(20)]
        result = fuzzy_search(items, "stop", key_fn=lambda x: x, limit=5)
        assert len(result) == 5

    def test_substring_match_bonus(self):
        """Test that substring matches get priority."""
        items = ["Odenplan", "Oden", "Ode"]
        result = fuzzy_search(items, "oden", key_fn=lambda x: x, threshold=0.5)
        # "Oden" is exact match, should be first
        assert result[0] == "Oden"


class TestUnifiedSearch:
    """Tests for unified search function."""

    def test_default_substring(self):
        """Test default mode is substring."""
        items = ["ABC", "ABCD", "XYZ"]
        result = search(items, "abc", key_fn=lambda x: x)
        assert len(result) == 2

    def test_explicit_substring_mode(self):
        """Test explicit substring mode."""
        items = ["ABC", "ABCD", "XYZ"]
        result = search(items, "abc", key_fn=lambda x: x, mode=SearchMode.SUBSTRING)
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

    def test_fuzzy_mode_with_threshold(self):
        """Test fuzzy mode respects threshold kwarg."""
        items = ["ABC", "XYZ"]
        # High threshold should filter out poor matches
        result = search(
            items,
            "QQQ",
            key_fn=lambda x: x,
            mode=SearchMode.FUZZY,
            threshold=0.9,
        )
        assert len(result) == 0


class TestSearchMode:
    """Tests for SearchMode enum."""

    def test_substring_value(self):
        """Test SUBSTRING enum value."""
        assert SearchMode.SUBSTRING.value == "substring"

    def test_fuzzy_value(self):
        """Test FUZZY enum value."""
        assert SearchMode.FUZZY.value == "fuzzy"
