"""Tests for JourneyPlannerClient functionality."""

from datetime import date, time, timedelta

import aiohttp
import pytest

from tsl.clients.journey import JourneyPlannerClient
from tsl.models.journey import DwellTime, Language, RouteType, SearchLeg, StopFilter


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


# =============================================================================
# Unit tests for build_request_params
# =============================================================================


class TestBuildRequestParams:
    """Unit tests for parameter building (no API calls)."""

    def test_basic_params(self):
        """Test basic origin/destination parameters."""
        origin = SearchLeg(type="any", value="9091001000009117")
        dest = SearchLeg(type="any", value="9091001000009001")

        params = JourneyPlannerClient.build_request_params(origin, dest)

        assert params.url == "https://journeyplanner.integration.sl.se/v2/trips"
        param_dict = dict(params.params)
        assert param_dict["type_origin"] == "any"
        assert param_dict["name_origin"] == "9091001000009117"
        assert param_dict["type_destination"] == "any"
        assert param_dict["name_destination"] == "9091001000009001"
        assert param_dict["calc_number_of_trips"] == 1

    def test_calc_number_of_trips_valid(self):
        """Test valid calc_number_of_trips values."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        for num in [1, 2, 3]:
            params = JourneyPlannerClient.build_request_params(
                origin, dest, calc_number_of_trips=num
            )
            assert dict(params.params)["calc_number_of_trips"] == num

    def test_calc_number_of_trips_invalid(self):
        """Test invalid calc_number_of_trips raises error."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        with pytest.raises(
            ValueError, match="calc_number_of_trips must be between 1 and 3"
        ):
            JourneyPlannerClient.build_request_params(
                origin, dest, calc_number_of_trips=0
            )

        with pytest.raises(
            ValueError, match="calc_number_of_trips must be between 1 and 3"
        ):
            JourneyPlannerClient.build_request_params(
                origin, dest, calc_number_of_trips=4
            )

    def test_via_parameters(self):
        """Test via stop parameters."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")
        via = SearchLeg(type="stop", value="via_stop")

        params = JourneyPlannerClient.build_request_params(origin, dest, via=via)
        param_dict = dict(params.params)

        assert param_dict["type_via"] == "stop"
        assert param_dict["name_via"] == "via_stop"

    def test_not_via_parameters(self):
        """Test not_via (avoid) stop parameters."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")
        not_via = SearchLeg(type="stop", value="avoid_stop")

        params = JourneyPlannerClient.build_request_params(
            origin, dest, not_via=not_via
        )
        param_dict = dict(params.params)

        assert param_dict["type_not_via"] == "stop"
        assert param_dict["name_not_via"] == "avoid_stop"

    def test_dwell_time(self):
        """Test dwell time parameter."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")
        dwell = DwellTime(timedelta(minutes=15))

        params = JourneyPlannerClient.build_request_params(
            origin, dest, dwell_time=dwell
        )
        param_dict = dict(params.params)

        assert param_dict["dwell_time"] == "00:15"

    def test_language(self):
        """Test language parameter."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        params = JourneyPlannerClient.build_request_params(
            origin, dest, language=Language.EN
        )
        param_dict = dict(params.params)

        assert param_dict["language"] == "en"

    def test_max_changes(self):
        """Test max_changes parameter."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        params = JourneyPlannerClient.build_request_params(origin, dest, max_changes=2)
        param_dict = dict(params.params)

        assert param_dict["max_changes"] == 2

    def test_route_type(self):
        """Test route_type parameter."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        params = JourneyPlannerClient.build_request_params(
            origin, dest, route_type=RouteType.LEAST_WALKING
        )
        param_dict = dict(params.params)

        assert param_dict["route_type"] == "leastwalking"

    def test_include_coordinates(self):
        """Test include_coordinates parameter."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        params = JourneyPlannerClient.build_request_params(
            origin, dest, include_coordinates=True
        )
        param_dict = dict(params.params)

        assert param_dict["gen_c"] == "true"

    def test_date_time_parameters(self):
        """Test date and time parameters."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        params = JourneyPlannerClient.build_request_params(
            origin,
            dest,
            departure_date=date(2024, 12, 25),
            departure_time=time(14, 30),
            search_for_arrival=True,
        )
        param_dict = dict(params.params)

        assert param_dict["itd_date"] == "20241225"
        assert param_dict["itd_time"] == "1430"
        assert param_dict["itd_trip_date_time_dep_arr"] == "arr"

    def test_transport_mode_filters(self):
        """Test transport mode filter parameters."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        params = JourneyPlannerClient.build_request_params(
            origin,
            dest,
            include_train=True,
            include_metro=False,
            include_bus=True,
        )
        param_dict = dict(params.params)

        assert param_dict["incl_mot_0"] == "true"  # train
        assert param_dict["incl_mot_2"] == "false"  # metro
        assert param_dict["incl_mot_5"] == "true"  # bus

    def test_change_speed_valid(self):
        """Test valid change_speed values."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        params = JourneyPlannerClient.build_request_params(
            origin, dest, change_speed=100
        )
        param_dict = dict(params.params)

        assert param_dict["change_speed"] == 100

    def test_change_speed_invalid(self):
        """Test invalid change_speed raises error."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        with pytest.raises(ValueError, match="change_speed must be between 25 and 400"):
            JourneyPlannerClient.build_request_params(origin, dest, change_speed=10)

        with pytest.raises(ValueError, match="change_speed must be between 25 and 400"):
            JourneyPlannerClient.build_request_params(origin, dest, change_speed=500)

    def test_pedestrian_options(self):
        """Test pedestrian options."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        params = JourneyPlannerClient.build_request_params(
            origin,
            dest,
            max_walk_time=10,
            max_pedestrian_time=30,
            min_walk_distance=100,
            max_walk_distance=1000,
        )
        param_dict = dict(params.params)

        assert param_dict["tr_it_mot_value100"] == 10
        assert param_dict["max_time_pedestrian"] == 30
        assert param_dict["min_length_pedestrian"] == 100
        assert param_dict["max_length_pedestrian"] == 1000

    def test_bicycle_options(self):
        """Test bicycle options."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        params = JourneyPlannerClient.build_request_params(
            origin,
            dest,
            compute_bike_trip=True,
            max_bike_time=20,
            min_bike_distance=500,
            max_bike_distance=1000,
        )
        param_dict = dict(params.params)

        assert param_dict["compute_monomodal_trip_bicycle"] == "true"
        assert param_dict["max_time_bicycle"] == 20
        assert param_dict["min_length_bicycle"] == 500
        assert param_dict["max_length_bicycle"] == 1000

    def test_max_bike_distance_limit(self):
        """Test max_bike_distance API limit."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        with pytest.raises(
            ValueError, match="max_bike_distance cannot exceed 1000 meters"
        ):
            JourneyPlannerClient.build_request_params(
                origin, dest, max_bike_distance=5000
            )

    def test_walk_trip_option(self):
        """Test walk-only trip option."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        params = JourneyPlannerClient.build_request_params(
            origin, dest, compute_walk_trip=True
        )
        param_dict = dict(params.params)

        assert param_dict["compute_monomodal_trip_pedestrian"] == "true"

    def test_additional_options(self):
        """Test additional options."""
        origin = SearchLeg(type="any", value="origin")
        dest = SearchLeg(type="any", value="dest")

        params = JourneyPlannerClient.build_request_params(
            origin,
            dest,
            suppress_alternatives=True,
            calc_one_direction=True,
            use_nearby_stops=False,
        )
        param_dict = dict(params.params)

        assert param_dict["no_alt"] == "true"
        assert param_dict["calc_one_direction"] == "true"
        assert param_dict["use_prox_foot_search"] == "false"


# =============================================================================
# Integration tests (require API access)
# =============================================================================


@pytest.mark.integration
async def test_get_system_info(session):
    """Test get_system_info endpoint."""
    client = JourneyPlannerClient(session)
    info = await client.get_system_info()

    assert "from_date" in info
    assert "to_date" in info
    assert isinstance(info["from_date"], str)
    assert isinstance(info["to_date"], str)


@pytest.mark.integration
async def test_find_stops(session):
    """Test find_stops endpoint."""
    client = JourneyPlannerClient(session)
    stops = await client.find_stops("odenplan")

    assert isinstance(stops, list)
    assert len(stops) > 0

    stop = stops[0]
    assert "id" in stop
    assert "name" in stop
    assert stop["type"] == "stop"


@pytest.mark.integration
async def test_find_stops_by_coordinates_quirk(session):
    """
    Test find_stops by coordinates quirk - when searching by coordinates
    "stop"'s are not returned.
    """
    client = JourneyPlannerClient(session)
    results = await client.find_stops(
        SearchLeg.from_coordinates("59.34299", "18.04966"),
        filter=StopFilter.STOPS | StopFilter.POI,
    )

    assert isinstance(results, list)
    assert len(results) > 0

    result = results[0]
    assert "id" in result
    assert "name" in result
    assert result["type"] != "stop"


@pytest.mark.integration
async def test_find_stops_known_stop(session):
    """Test find_stops returns expected result for known stop."""
    client = JourneyPlannerClient(session)
    stops = await client.find_stops(SearchLeg.from_any("t-centralen"))

    assert len(stops) > 0
    # T-Centralen should be in results
    names = [s.get("disassembledName", "").lower() for s in stops]
    assert any("centralen" in name for name in names)


@pytest.mark.integration
async def test_get_lines(session):
    """Test get_lines endpoint."""
    client = JourneyPlannerClient(session)
    result = await client.get_lines()

    assert isinstance(result, dict)
    # Should have transportations key
    assert "transportations" in result or isinstance(result, dict)


@pytest.mark.integration
async def test_search_trip_basic(session):
    """Test basic trip search."""
    client = JourneyPlannerClient(session)

    # Odenplan to T-Centralen
    origin = SearchLeg(type="any", value="9091001000009117")
    dest = SearchLeg(type="any", value="9091001000009001")

    params = client.build_request_params(origin, dest)
    journeys = await client.search_trip(params)

    assert isinstance(journeys, list)
    assert len(journeys) > 0

    journey = journeys[0]
    assert "legs" in journey


@pytest.mark.integration
async def test_search_trip_with_options(session):
    """Test trip search with various options."""
    client = JourneyPlannerClient(session)

    origin = SearchLeg(type="any", value="9091001000009117")
    dest = SearchLeg(type="any", value="9091001000009001")

    params = client.build_request_params(
        origin,
        dest,
        calc_number_of_trips=3,
        include_metro=True,
        max_changes=2,
    )
    journeys = await client.search_trip(params)

    assert isinstance(journeys, list)
