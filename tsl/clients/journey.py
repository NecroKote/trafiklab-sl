from datetime import date, time
from typing import Any, Dict, List, cast

from tsl.models.journey import (
    DwellTime,
    Journey,
    Language,
    RouteType,
    SearchLeg,
    SearchType,
    StopFilter,
    SystemValidity,
)
from tsl.models.stops import StopFinderType

from .common import AsyncClient, OperationFailed, ResponseFormatChanged, UrlParams


def _str_bool(value: bool) -> str:
    """Convert boolean to lowercase string for API parameters."""
    return "true" if value else "false"


class JourneyPlannerClient(AsyncClient):
    """
    client for SL Journey Planner v2 API
    https://www.trafiklab.se/api/our-apis/sl/journey-planner-2/
    """

    BASE_URL = "https://journeyplanner.integration.sl.se/v2"

    async def get_system_info(self) -> SystemValidity | None:
        """
        Get route planning data availability period.

        Returns:
            SystemValidity with from_date and to_date fields
        """
        args = UrlParams(f"{self.BASE_URL}/system-info", None)
        response = await self._request_json(args)

        if validity := response.get("validity"):
            return cast(SystemValidity, validity)

    async def find_stops(
        self, query: str | SearchLeg, filter: StopFilter = StopFilter.STOPS
    ) -> List[StopFinderType]:
        """
        Search for stops, addresses, or points of interest by name or coordinates.

        Args:
            query: Search query (e.g., "odenplan", "t-centralen"), or SearchLeg
            filter: allows limiting results to specific types (default: stops only)

        **WARNING**: the API may ignore `filter` when querying by coordinates

        Returns:
            List of StopLocation objects sorted by match quality

        Example:
            stops = await client.find_stops("odenplan")
            # Use SearchLeg.from_stop_finder(stops[0]) for journey planning
        """

        if isinstance(query, str):
            query = SearchLeg.from_any(query)

        params: List[tuple[str, Any]] = [
            ("any_obj_filter_sf", filter.value),
        ]

        if query.type == SearchType.COORD:
            params.append(("name_sf", query.value))
            params.append(("type_sf", "coord"))
        else:
            params.append(("name_sf", query.value))
            params.append(("type_sf", "any"))

        args = UrlParams(f"{self.BASE_URL}/stop-finder", params)
        response = await self._request_json(args)

        if (locations := response.get("locations")) is None:
            raise ResponseFormatChanged("'ResponseData' not found in response")

        locations = cast(List[StopFinderType], locations)
        # use matchQuality for sorting if available
        return sorted(locations, key=lambda x: x.get("matchQuality", 0), reverse=True)

    @classmethod
    def build_request_params(
        cls,
        origin: SearchLeg,
        destination: SearchLeg,
        calc_number_of_trips: int = 1,
        via: SearchLeg | None = None,
        not_via: SearchLeg | None = None,
        dwell_time: DwellTime | None = None,
        language: Language | None = None,
        max_changes: int | None = None,
        route_type: RouteType | None = None,
        include_coordinates: bool | None = None,
        # Date/time parameters
        departure_date: date | None = None,
        departure_time: time | None = None,
        search_for_arrival: bool = False,
        # Transport mode filters (True=include, False=exclude, None=default)
        include_train: bool | None = None,  # incl_mot_0 - Pendeltåg
        include_metro: bool | None = None,  # incl_mot_2 - Tunnelbana
        include_tram: bool | None = None,  # incl_mot_4 - Lokaltåg/Spårväg
        include_bus: bool | None = None,  # incl_mot_5 - Buss
        include_ship: bool | None = None,  # incl_mot_9 - Båttrafik
        include_on_demand: bool | None = None,  # incl_mot_10 - Anropsstyrd
        include_national_train: bool | None = None,  # incl_mot_14 - Fjärrtåg
        include_accessible_bus: bool | None = None,  # incl_mot_19 - Närtrafik
        # Additional parameters
        change_speed: int | None = None,  # 25-400 (percentage)
        suppress_alternatives: bool | None = None,  # no_alt
        calc_one_direction: bool | None = None,
        use_nearby_stops: bool | None = None,  # use_prox_foot_search
        # Pedestrian options
        max_walk_time: int | None = None,  # tr_it_mot_value100 (minutes)
        max_pedestrian_time: int | None = None,  # max_time_pedestrian (minutes)
        min_walk_distance: int | None = None,  # min_length_pedestrian (meters)
        max_walk_distance: int | None = None,  # max_length_pedestrian (meters)
        # Bicycle options
        compute_bike_trip: bool | None = None,  # compute_monomodal_trip_bicycle
        max_bike_time: int | None = None,  # max_time_bicycle (minutes)
        min_bike_distance: int | None = None,  # min_length_bicycle (meters)
        max_bike_distance: int | None = None,  # max_length_bicycle (meters)
        # Walk-only option
        compute_walk_trip: bool | None = None,  # compute_monomodal_trip_pedestrian
    ) -> UrlParams:
        """
        Build request parameters for journey planner API.

        Args:
            origin: Origin location (stop ID or coordinates)
            destination: Destination location (stop ID or coordinates)
            calc_number_of_trips: Number of trips to calculate (1-3)
            via: Optional stop to route through
            not_via: Optional stop to avoid
            dwell_time: Extra waiting time at via stop
            language: Response language (sv/en)
            max_changes: Maximum number of interchanges (0-9)
            route_type: Optimization preference (leasttime/leastinterchange/leastwalking)
            include_coordinates: Include coordinate sequences for trip legs
            departure_date: Date of departure/arrival
            departure_time: Time of departure/arrival
            search_for_arrival: If True, search by arrival time instead of departure
            include_train: Include commuter trains (pendeltåg)
            include_metro: Include metro (tunnelbana)
            include_tram: Include tram/local trains (spårväg/lokaltåg)
            include_bus: Include buses
            include_ship: Include ships and ferries
            include_on_demand: Include on-demand transit
            include_national_train: Include national/long-distance trains
            include_accessible_bus: Include accessible bus (närtrafik)
            change_speed: Walking speed percentage (25-400)
            suppress_alternatives: Suppress alternative/additional trips
            calc_one_direction: Don't calculate trip before requested time
            use_nearby_stops: Allow walking to nearby stops
            max_walk_time: Max time for walking at trip start/end (minutes)
            max_pedestrian_time: Max time for walk-only trip (minutes)
            min_walk_distance: Min distance for footpath sections (meters)
            max_walk_distance: Max distance for footpath sections (meters)
            compute_bike_trip: Calculate additional bike-only trip
            max_bike_time: Max time for bike-only trip (minutes)
            min_bike_distance: Min distance for bike sections (meters)
            max_bike_distance: Max distance for bike sections (meters)
            compute_walk_trip: Calculate additional walk-only trip

        Returns:
            UrlParams ready for search_trip()
        """

        if calc_number_of_trips > 3 or calc_number_of_trips < 1:
            raise ValueError("calc_number_of_trips must be between 1 and 3")

        params: List[tuple[str, Any]] = [
            ("type_origin", origin.type),
            ("name_origin", origin.value),
            ("type_destination", destination.type),
            ("name_destination", destination.value),
            ("calc_number_of_trips", calc_number_of_trips),
        ]

        if via is not None:
            params.append(("type_via", via.type))
            params.append(("name_via", via.value))

        if not_via is not None:
            params.append(("type_not_via", not_via.type))
            params.append(("name_not_via", not_via.value))

        if dwell_time is not None:
            params.append(("dwell_time", dwell_time.to_hh_mm()))

        if language is not None:
            params.append(("language", language))

        if max_changes is not None:
            params.append(("max_changes", max_changes))

        if route_type is not None:
            params.append(("route_type", route_type.value))

        if include_coordinates is not None:
            params.append(("gen_c", _str_bool(include_coordinates)))

        # Date/time parameters
        if departure_date is not None:
            params.append(("itd_date", departure_date.strftime("%Y%m%d")))

        if departure_time is not None:
            params.append(("itd_time", departure_time.strftime("%H%M")))

        if search_for_arrival:
            params.append(("itd_trip_date_time_dep_arr", "arr"))

        # Transport mode filters
        if include_train is not None:
            params.append(("incl_mot_0", _str_bool(include_train)))

        if include_metro is not None:
            params.append(("incl_mot_2", _str_bool(include_metro)))

        if include_tram is not None:
            params.append(("incl_mot_4", _str_bool(include_tram)))

        if include_bus is not None:
            params.append(("incl_mot_5", _str_bool(include_bus)))

        if include_ship is not None:
            params.append(("incl_mot_9", _str_bool(include_ship)))

        if include_on_demand is not None:
            params.append(("incl_mot_10", _str_bool(include_on_demand)))

        if include_national_train is not None:
            params.append(("incl_mot_14", _str_bool(include_national_train)))

        if include_accessible_bus is not None:
            params.append(("incl_mot_19", _str_bool(include_accessible_bus)))

        # Additional parameters
        if change_speed is not None:
            if not 25 <= change_speed <= 400:
                raise ValueError("change_speed must be between 25 and 400")
            params.append(("change_speed", change_speed))

        if suppress_alternatives is not None:
            params.append(("no_alt", _str_bool(suppress_alternatives)))

        if calc_one_direction is not None:
            params.append(("calc_one_direction", _str_bool(calc_one_direction)))

        if use_nearby_stops is not None:
            params.append(("use_prox_foot_search", _str_bool(use_nearby_stops)))

        # Pedestrian options
        if max_walk_time is not None:
            params.append(("tr_it_mot_value100", max_walk_time))

        if max_pedestrian_time is not None:
            params.append(("max_time_pedestrian", max_pedestrian_time))

        if min_walk_distance is not None:
            params.append(("min_length_pedestrian", min_walk_distance))

        if max_walk_distance is not None:
            params.append(("max_length_pedestrian", max_walk_distance))

        # Bicycle options
        if compute_bike_trip is not None:
            params.append(
                ("compute_monomodal_trip_bicycle", _str_bool(compute_bike_trip))
            )

        if max_bike_time is not None:
            params.append(("max_time_bicycle", max_bike_time))

        if min_bike_distance is not None:
            params.append(("min_length_bicycle", min_bike_distance))

        if max_bike_distance is not None:
            if max_bike_distance > 1000:
                raise ValueError(
                    "max_bike_distance cannot exceed 1000 meters (API limit)"
                )
            params.append(("max_length_bicycle", max_bike_distance))

        # Walk-only trip
        if compute_walk_trip is not None:
            params.append(
                ("compute_monomodal_trip_pedestrian", _str_bool(compute_walk_trip))
            )

        return UrlParams(f"{cls.BASE_URL}/trips", params)

    async def search_trip(self, params: UrlParams) -> List[Journey]:
        """
        Search for trips using pre-built parameters.

        Args:
            params: UrlParams from build_request_params()

        Returns:
            List of Journey objects

        Raises:
            OperationFailed: If API returns error messages
            ResponseFormatChanged: If response format is unexpected
        """
        response = await self._request_json(params)

        if (journeys := response.get("journeys")) is None:
            if messages := response.get("systemMessages"):
                filtered_errors = [
                    x["text"]
                    for x in messages
                    if x["type"] == "error" and x["code"] != -8010
                ]
                raise OperationFailed(filtered_errors)

            raise ResponseFormatChanged(
                "Response format has changed, expected 'journeys' or `systemMessages` keys in response"
            )

        return journeys

    async def get_lines(
        self,
        branch_code: int | None = None,
        merge_directions: bool | None = None,
    ) -> Dict[str, Any]:
        """
        Get list of lines.

        Note: The SL Transport API provides the same functionality in an easier way.

        Args:
            branch_code: Filter by transport type:
                1 = Bus, 2 = Metro, 3 = Tram/local train, 4 = Commuter train,
                5 = Road ferry, 6 = Vessel service, 7 = Taxi, 8 = Accessible bus
            merge_directions: Merge line directions

        Returns:
            Dict with 'transportations' key containing line items
        """
        params: List[tuple[str, Any]] = [("line_list_subnetwork", "tfs")]

        if branch_code is not None:
            params.append(("line_list_branch_code", branch_code))

        if merge_directions is not None:
            params.append(("merge_dir", _str_bool(merge_directions)))

        args = UrlParams(f"{self.BASE_URL}/line-list", params)
        return await self._request_json(args)
