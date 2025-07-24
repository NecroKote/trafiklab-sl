from typing import List, cast
from enum import IntFlag

from ..models.stops import StopFinderType
from .common import AsyncClient, ResponseFormatChanged, UrlParams


class Filter(IntFlag):
    STOPS = 2
    STREET = 4
    ADDRESS = 8
    POI = 32

class StopLookupClient(AsyncClient):
    """
    client for SL Stop Lookup API
    https://www.trafiklab.se/sv/api/our-apis/sl/journey-planner-2/
    """

    @staticmethod
    def _get_request_url_params(search_string: str, filter: Filter = Filter.STOPS) -> UrlParams:
        """returns url and params to request stops"""

        params = [
            ("name_sf", search_string),
            ("type_sf", "any"),
            ("any_obj_filter_sf", str(filter.value)),
        ]

        return UrlParams(
            "https://journeyplanner.integration.sl.se/v2/stop-finder",
            params,
        )

    async def _request_matches(self, args: UrlParams) -> List[StopFinderType]:
        response = await self._request_json(args)

        if (locations := response.get("locations")) is None:
            raise ResponseFormatChanged("'ResponseData' not found in response")

        locations = cast(List[StopFinderType], locations)
        return sorted(locations, key=lambda x: x["matchQuality"], reverse=True)

    async def get_stops(self, search_string: str) -> List[StopFinderType]:
        """
        Get stops by search string
        """

        args = self._get_request_url_params(search_string)
        return await self._request_matches(args)

    async def get_address(self, search_string: str) -> List[StopFinderType]:
        """
        Get street or address by search string
        """

        args = self._get_request_url_params(search_string, filter=Filter.STREET | Filter.ADDRESS)
        return await self._request_matches(args)
