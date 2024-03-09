from typing import Optional
from urllib.parse import quote

import aiohttp

from tsl.models.departures import SiteDepartureResponse, TransportMode

from .common import AsyncClient, UrlParams

__all__ = ("TransportClient",)


class TransportClient(AsyncClient):
    """
    client for SL Transport API
    https://www.trafiklab.se/api/trafiklab-apis/sl/transport/

    only departures are supported at the moment
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
        params = {}
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
        args = self.get_departures_url_params(
            site_id, transport, direction, line, forecast
        )

        if session:
            response = await self._request_json(session, args)
        else:
            async with self.session as new_session:
                response = await self._request_json(new_session, args)

        return SiteDepartureResponse.schema().load(response)
