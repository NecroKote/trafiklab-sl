from typing import Any, Dict, List, Optional, cast
from urllib.parse import quote

from ..models.common import LineId
from ..models.departures import SiteDepartureResponse, TransportMode
from ..models.sites import Site
from ..models.transport import Line, LinesResponse, StopPoint, TransportAuthority
from .common import AsyncClient, ResponseFormatChanged, UrlParams

__all__ = ("TransportClient",)


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

    async def get_transport_authorities(self) -> List[TransportAuthority]:
        """
        List all transport authorities within Region Stockholm.

        Returns:
            List of TransportAuthority objects
        """
        args = UrlParams(f"{self.BASE_URL}/transport-authorities", None)
        response = await self._request_json(args)
        return cast(List[TransportAuthority], response)

    async def get_lines(
        self, transport_authority_id: int = 1
    ) -> Dict[TransportMode, List[Line]]:
        """
        List all lines within Region Stockholm.

        Args:
            transport_authority_id: Filter by transport authority (default: 1 for SL)

        Returns:
            dict with lines grouped by TransportMode
        """
        args = UrlParams(
            f"{self.BASE_URL}/lines",
            {"transport_authority_id": transport_authority_id},
        )
        response = await self._request_json(args)
        lines = cast(LinesResponse, response)

        try:
            result = {
                TransportMode.METRO: lines["metro"],
                TransportMode.TRAM: lines["tram"],
                TransportMode.TRAIN: lines["train"],
                TransportMode.BUS: lines["bus"],
                TransportMode.SHIP: lines["ship"],
                TransportMode.FERRY: lines["ferry"],
                TransportMode.TAXI: lines["taxi"],
            }
        except KeyError as e:
            raise ResponseFormatChanged(f"Missing expected key in lines response: {e}")

        return result

    async def get_sites(self, expand: bool = False) -> List[Site]:
        """
        List all sites within Region Stockholm.

        **WARNING**: This endpoint returns a large amount of data.

        Args:
            expand: If True, expand referenced objects (affects response time/size)

        Returns:
            List of Site objects
        """
        params: Dict[str, Any] = {}
        if expand:
            params["expand"] = "true"

        args = UrlParams(f"{self.BASE_URL}/sites", params or None)
        response = await self._request_json(args)
        return cast(List[Site], response)

    async def get_stop_points(self) -> List[StopPoint]:
        """
        List all stop points (platforms) within Region Stockholm.

        **WARNING**: This endpoint returns a large amount of data.

        Returns:
            List of StopPoint objects
        """
        args = UrlParams(f"{self.BASE_URL}/stop-points", None)
        response = await self._request_json(args)
        return cast(List[StopPoint], response)
