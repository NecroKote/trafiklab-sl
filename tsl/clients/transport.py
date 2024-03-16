from typing import Any, Optional
from urllib.parse import quote

import aiohttp

from tsl.models.departures import SiteDepartureResponse, TransportMode
from tsl.models.sites import Site

from .common import AsyncClient, UrlParams

__all__ = ("TransportClient",)


class TransportClient(AsyncClient):
    """
    client for SL Transport API
    https://www.trafiklab.se/api/trafiklab-apis/sl/transport/

    only departures and sites are supported at the moment
    """

    @staticmethod
    def get_departures_url_params(
        site_id: int,
        transport: Optional[TransportMode] = None,
        direction: Optional[int] = None,
        line: Optional[int] = None,
        forecast: int = 60,
    ) -> UrlParams:
        url = (
            "https://transport.integration.sl.se"
            f"/v1/sites/{quote(str(site_id))}/departures"
        )
        params: dict[str, Any] = {}
        if transport is not None:
            params["transport"] = transport.value
        if direction is not None:
            params["direction"] = direction
        if line is not None:
            params["line"] = line
        if forecast is not None:
            params["forecast"] = forecast

        return UrlParams(url, params)

    async def get_site_departures(
        self,
        site_id: int,
        transport: Optional[TransportMode] = None,
        direction: Optional[int] = None,
        line: Optional[int] = None,
        forecast: int = 60,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> SiteDepartureResponse:
        """
        Get upcoming departures and deviations starting from time of
        the request (a maximum of 3 departures for each line & direction)
        """

        args = self.get_departures_url_params(
            site_id, transport, direction, line, forecast
        )

        if session:
            response = await self._request_json(session, args)
        else:
            async with self.session as new_session:
                response = await self._request_json(new_session, args)

        return SiteDepartureResponse.schema().load(response)

    async def get_sites(self, session: Optional[aiohttp.ClientSession] = None):
        """List all sites within Region Stockholm"""

        args = UrlParams("https://transport.integration.sl.se/v1/sites", None)

        if session:
            response = await self._request_json(session, args)
        else:
            async with self.session as new_session:
                response = await self._request_json(new_session, args)

        return Site.schema().load(response, many=True)
