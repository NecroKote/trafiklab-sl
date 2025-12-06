"""Tests for TransportClient functionality."""

import aiohttp
import pytest

from tsl.clients.transport import TransportClient
from tsl.models.departures import TransportMode


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


# =============================================================================
# Unit tests for URL parameter building
# =============================================================================


class TestGetDeparturesUrlParams:
    """Unit tests for departures URL parameter building."""

    def test_basic_params(self):
        """Test basic site_id parameter."""
        params = TransportClient.get_departures_url_params(site_id=9001)

        assert "9001" in params.url
        assert params.params == {}

    def test_with_transport_filter(self):
        """Test transport mode filter."""
        params = TransportClient.get_departures_url_params(
            site_id=9001, transport=TransportMode.METRO
        )

        assert params.params["transport"] == "METRO"

    def test_with_direction(self):
        """Test direction filter."""
        params = TransportClient.get_departures_url_params(site_id=9001, direction=1)

        assert params.params["direction"] == 1

    def test_with_line_int(self):
        """Test line filter with integer."""
        params = TransportClient.get_departures_url_params(site_id=9001, line=17)

        assert params.params["line"] == "17"

    def test_with_line_str(self):
        """Test line filter with string."""
        params = TransportClient.get_departures_url_params(site_id=9001, line="176")

        assert params.params["line"] == "176"

    def test_with_forecast(self):
        """Test forecast time window."""
        params = TransportClient.get_departures_url_params(site_id=9001, forecast=120)

        assert params.params["forecast"] == 120

    def test_all_params(self):
        """Test all parameters combined."""
        params = TransportClient.get_departures_url_params(
            site_id=9117,
            transport=TransportMode.BUS,
            direction=2,
            line=55,
            forecast=90,
        )

        assert "9117" in params.url
        assert params.params["transport"] == "BUS"
        assert params.params["direction"] == 2
        assert params.params["line"] == "55"
        assert params.params["forecast"] == 90


# =============================================================================
# Integration tests (require API access)
# =============================================================================


@pytest.mark.integration
async def test_get_lines(session):
    """Test get_lines endpoint."""
    client = TransportClient(session)
    lines = await client.get_lines()

    assert isinstance(lines, dict)
    # Should have transport mode categories
    possible_keys = ["metro", "tram", "train", "bus", "ship", "ferry", "taxi"]
    assert any(key in lines for key in possible_keys)


@pytest.mark.integration
async def test_get_lines_specific_mode(session):
    """Test get_lines returns data for specific modes."""
    client = TransportClient(session)
    lines = await client.get_lines()

    # Check metro lines exist
    if "metro" in lines:
        assert isinstance(lines["metro"], list)
        if lines["metro"]:
            line = lines["metro"][0]
            assert "id" in line
            assert "designation" in line


@pytest.mark.integration
async def test_get_sites(session):
    """Test get_sites endpoint."""
    client = TransportClient(session)
    sites = await client.get_sites()

    assert isinstance(sites, list)
    assert len(sites) > 0

    site = sites[0]
    assert "id" in site
    assert "name" in site


@pytest.mark.integration
async def test_get_sites_expanded(session):
    """Test get_sites with expand parameter."""
    client = TransportClient(session)
    sites = await client.get_sites(expand=True)

    assert isinstance(sites, list)
    assert len(sites) > 0


@pytest.mark.integration
async def test_get_stop_points(session):
    """Test get_stop_points endpoint."""
    client = TransportClient(session)
    stop_points = await client.get_stop_points()

    assert isinstance(stop_points, list)
    assert len(stop_points) > 0

    stop_point = stop_points[0]
    assert "id" in stop_point
    assert "name" in stop_point


@pytest.mark.integration
async def test_get_transport_authorities(session):
    """Test get_transport_authorities endpoint."""
    client = TransportClient(session)
    authorities = await client.get_transport_authorities()

    assert isinstance(authorities, list)
    assert len(authorities) > 0

    authority = authorities[0]
    assert "id" in authority
    assert "name" in authority


@pytest.mark.integration
async def test_get_site_departures(session):
    """Test get_site_departures endpoint."""
    client = TransportClient(session)
    # Odenplan site_id
    response = await client.get_site_departures(9117)

    assert "departures" in response
    assert "stop_deviations" in response
    assert isinstance(response["departures"], list)


@pytest.mark.integration
async def test_get_site_departures_with_filters(session):
    """Test get_site_departures with filters."""
    client = TransportClient(session)
    response = await client.get_site_departures(
        site_id=9117,
        transport=TransportMode.METRO,
        forecast=30,
    )

    assert "departures" in response
    assert isinstance(response["departures"], list)
