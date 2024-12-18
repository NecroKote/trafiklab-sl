import pytest

from tsl.models.stops import LookupSiteId


@pytest.mark.parametrize(
    "inp,expected",
    [
        ("300100000", 0),
        ("300109001", 9001),
        ("321134567", 1234567),
    ],
)
def test_lookup_siteid_transport_siteid(inp, expected):
    result = LookupSiteId(inp)
    assert result.transport_siteid == expected


@pytest.mark.parametrize(
    "inp,expected",
    [
        ("0", "300100000"),
        ("9001", "300109001"),
        ("1234567", "321134567"),
        ("300109001", "300109001"),
    ],
)
def test_lookup_siteid(inp, expected):
    result = LookupSiteId.from_siteid(inp)
    assert result == expected
