from typing import List, Optional

import aiohttp

from ..models.stops import Stop
from .common import AsyncClient, UrlParams


class StopLookupClient(AsyncClient):
    """
    client for SL Stop Lookup API
    https://www.trafiklab.se/api/trafiklab-apis/sl/stop-lookup/
    """

    def __init__(self, api_key: str):
        """
        :param api_key: the "SL Platsuppslag" API key
        """

        super().__init__()
        self._api_key = api_key

    @staticmethod
    def get_request_url_params(
        api_key: str,
        search_string: str,
        max_results: int = 10,
    ) -> UrlParams:
        """returns url and params to request stops"""

        if len(search_string) > 20:
            raise ValueError("search_string too long. max 20 characters")

        if max_results < 1 or max_results >= 50:
            raise ValueError("max_results must be between 1 and 50")

        params = [
            ("key", api_key),
            ("searchstring", search_string),
            ("maxresults", str(max_results)),
            ("type", "S"),  # "Stations only"
        ]

        return UrlParams(
            "https://journeyplanner.integration.sl.se/v1/typeahead.json",
            params,
        )

    async def get_stops(
        self,
        search_string: str,
        max_results: int = 10,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Stop]:
        """
        Get stops by search string
        """

        args = self.get_request_url_params(self._api_key, search_string, max_results)

        if session:
            response = await self._request_json(session, args)
        else:
            async with self.session as new_session:
                response = await self._request_json(new_session, args)

        data = response["ResponseData"]

        return Stop.schema().load(data, many=True)
