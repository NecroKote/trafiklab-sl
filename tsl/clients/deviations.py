from typing import List, Optional

import aiohttp

from tsl.models.deviations import Deviation, TransportMode

from .common import AsyncClient, UrlParams

__all__ = ("DeviationsClient",)


class DeviationsClient(AsyncClient):
    """
    client for SL Deviations API
    https://www.trafiklab.se/api/trafiklab-apis/sl/deviations/#/
    """

    @staticmethod
    def get_request_url_params(
        future: Optional[bool] = None,
        site: Optional[List[int]] = None,
        line: Optional[List[str]] = None,
        transport_authority: Optional[int] = None,
        transport_mode: Optional[TransportMode] = None,
    ) -> UrlParams:
        """returns url and params to request deviations"""

        params = {}
        if future is not None:
            params["future"] = future
        if site is not None:
            params["site"] = ",".join((str(x) for x in site))
        if line is not None:
            params["line"] = ",".join((x for x in line))
        if transport_authority is not None:
            params["transport_authority"] = transport_authority
        if transport_mode is not None:
            params["transport_mode"] = ",".join((x.value for x in transport_mode))

        return UrlParams("https://deviations.integration.sl.se/v1/messages", params)

    async def get_deviations(
        self,
        future: Optional[bool] = None,
        site: Optional[List[int]] = None,
        line: Optional[List[str]] = None,
        transport_authority: Optional[int] = None,
        transport_mode: Optional[TransportMode] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Deviation]:

        args = self.get_request_url_params(
            future, site, line, transport_authority, transport_mode
        )

        if session:
            response = await self._request_json(session, args)
        else:
            async with self.session as new_session:
                response = await self._request_json(new_session, args)

        return Deviation.schema().load(response, many=True)
