from typing import Any, Dict, List, Optional, TypedDict, Union, cast
from urllib.parse import quote

from ..models.departures import SiteDepartureResponse, TransportMode
from ..models.sites import Site
from .common import AsyncClient, UrlParams

__all__ = ("TransportClient",)

# Line IDs are numeric but can be passed as int or str (e.g., 176 or "176")
LineId = Union[str, int]


class TransportAuthority(TypedDict):
    """Transport authority reference."""

    id: int
    name: str


class TransportAuthorityFull(TypedDict, total=False):
    """Full transport authority information."""

    id: int
    gid: int
    name: str
    formal_name: str
    code: str
    street: str
    postal_code: int
    city: str
    country: str
    valid: Dict[str, str]


class Contractor(TypedDict):
    """Line contractor information."""

    id: int
    name: str


class Line(TypedDict, total=False):
    """Line information from the lines endpoint."""

    id: int
    gid: int
    name: str
    designation: str
    transport_mode: str
    group_of_lines: str
    transport_authority: TransportAuthority
    contractor: Contractor
    valid: Dict[str, str]


class LinesResponse(TypedDict, total=False):
    """Response from /lines endpoint, grouped by transport mode."""

    metro: List[Line]
    tram: List[Line]
    train: List[Line]
    bus: List[Line]
    ship: List[Line]
    ferry: List[Line]
    taxi: List[Line]


class StopArea(TypedDict, total=False):
    """Stop area information."""

    id: int
    name: str
    sname: str
    type: str


class StopPoint(TypedDict, total=False):
    """Stop point information from the stop-points endpoint."""

    id: int
    gid: int
    pattern_point_gid: int
    name: str
    sname: str
    designation: str
    local_num: int
    type: str
    has_entrance: bool
    lat: float
    lon: float
    door_orientation: float
    transport_authority: TransportAuthority
    stop_area: StopArea
    valid: Dict[str, str]


class TransportClient(AsyncClient):
    """
    Client for SL Transport API.

    https://www.trafiklab.se/api/our-apis/sl/transport/

    Provides access to:
    - Lines: List all lines within Region Stockholm
    - Sites: List all sites (stations/stops)
    - Departures: Real-time departures from a site
    - Stop Points: List all stop points (platforms)
    - Transport Authorities: List all transport authorities
    """

    BASE_URL = "https://transport.integration.sl.se/v1"

    # -------------------------------------------------------------------------
    # Lines endpoint
    # -------------------------------------------------------------------------

    async def get_lines(self, transport_authority_id: int = 1) -> LinesResponse:
        """
        List all lines within Region Stockholm.

        Args:
            transport_authority_id: Filter by transport authority (default: 1 for SL)

        Returns:
            LinesResponse with lines grouped by transport mode:
            - metro, tram, train, bus, ship, ferry, taxi
        """
        args = UrlParams(
            f"{self.BASE_URL}/lines",
            {"transport_authority_id": transport_authority_id},
        )
        response = await self._request_json(args)
        return cast(LinesResponse, response)

    # -------------------------------------------------------------------------
    # Sites endpoint
    # -------------------------------------------------------------------------

    async def get_sites(self, expand: bool = False) -> List[Site]:
        """
        List all sites within Region Stockholm.

        Args:
            expand: If True, expand referenced objects (affects response time/size)

        Returns:
            List of Site objects with id, gid, name, lat, lon, stop_areas, valid period
        """
        params: Dict[str, Any] = {}
        if expand:
            params["expand"] = "true"

        args = UrlParams(f"{self.BASE_URL}/sites", params or None)
        response = await self._request_json(args)
        return cast(List[Site], response)

    # -------------------------------------------------------------------------
    # Departures endpoint
    # -------------------------------------------------------------------------

    @classmethod
    def get_departures_url_params(
        cls,
        site_id: int,
        transport: Optional[TransportMode] = None,
        direction: Optional[int] = None,
        line: Optional[LineId] = None,
        forecast: Optional[int] = None,
    ) -> UrlParams:
        """
        Build URL parameters for departures request.

        Args:
            site_id: ID of the site
            transport: Filter by transport mode (BUS, TRAM, METRO, TRAIN, FERRY, SHIP, TAXI)
            direction: Filter by line direction code
            line: Filter by line ID (e.g., 17 or "17")
            forecast: Time window in minutes for departures (default: API decides)

        Returns:
            UrlParams ready for request
        """
        url = f"{cls.BASE_URL}/sites/{quote(str(site_id))}/departures"
        params: dict[str, Any] = {}
        if transport is not None:
            params["transport"] = transport.value
        if direction is not None:
            params["direction"] = direction
        if line is not None:
            params["line"] = str(line)
        if forecast is not None:
            params["forecast"] = forecast

        return UrlParams(url, params)

    async def get_site_departures(
        self,
        site_id: int,
        transport: Optional[TransportMode] = None,
        direction: Optional[int] = None,
        line: Optional[LineId] = None,
        forecast: Optional[int] = None,
    ) -> SiteDepartureResponse:
        """
        Get upcoming departures and deviations from a site.

        Returns a maximum of 3 departures for each line & direction.

        Args:
            site_id: ID of the site (from get_sites())
            transport: Filter by transport mode (BUS, TRAM, METRO, TRAIN, FERRY, SHIP, TAXI)
            direction: Filter by line direction code
            line: Filter by line ID (e.g., 17 or "17")
            forecast: Time window in minutes (default: API decides, max departures still 3 per line)

        Returns:
            SiteDepartureResponse with:
            - departures: List of upcoming departures
            - stop_deviations: List of active deviations at this stop
        """
        args = self.get_departures_url_params(
            site_id, transport, direction, line, forecast
        )

        response = await self._request_json(args)
        return cast(SiteDepartureResponse, response)

    # -------------------------------------------------------------------------
    # Stop Points endpoint
    # -------------------------------------------------------------------------

    async def get_stop_points(self) -> List[StopPoint]:
        """
        List all stop points (platforms) within Region Stockholm.

        Returns:
            List of StopPoint objects with:
            - id, gid, pattern_point_gid
            - name, sname, designation
            - type (PLATFORM, etc.)
            - lat, lon, door_orientation
            - transport_authority, stop_area
            - valid period
        """
        args = UrlParams(f"{self.BASE_URL}/stop-points", None)
        response = await self._request_json(args)
        return cast(List[StopPoint], response)

    # -------------------------------------------------------------------------
    # Transport Authorities endpoint
    # -------------------------------------------------------------------------

    async def get_transport_authorities(self) -> List[TransportAuthorityFull]:
        """
        List all transport authorities within Region Stockholm.

        Returns:
            List of TransportAuthorityFull objects with:
            - id, gid, name, formal_name
            - code, street, postal_code, city, country
            - valid period
        """
        args = UrlParams(f"{self.BASE_URL}/transport-authorities", None)
        response = await self._request_json(args)
        return cast(List[TransportAuthorityFull], response)
