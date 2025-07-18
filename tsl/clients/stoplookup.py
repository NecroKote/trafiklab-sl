from typing import List, cast

from ..models.stops import StopFinderType
from .common import AsyncClient, ResponseFormatChanged, UrlParams


class StopLookupClient(AsyncClient):
    """
    client for SL Stop Lookup API
    https://www.trafiklab.se/sv/api/our-apis/sl/journey-planner-2/
    """

    @staticmethod
    def _get_request_url_params(search_string: str) -> UrlParams:
        """returns url and params to request stops"""

        if len(search_string) > 20:
            raise ValueError("search_string too long. max 20 characters")

        params = [
            ("name_sf", search_string),
            ("type_sf", "any"),
            ("any_obj_filter_sf", "2"),  # 2 = stops only
        ]

        return UrlParams(
            "https://journeyplanner.integration.sl.se/v2/stop-finder",
            params,
        )

    async def get_stops(self, search_string: str) -> List[StopFinderType]:
        """
        Get stops by search string
        """

        args = self._get_request_url_params(search_string)
        response = await self._request_json(args)

        if (locations := response.get("locations")) is None:
            raise ResponseFormatChanged("'ResponseData' not found in response")

        locations = cast(list[StopFinderType], locations)
        return sorted(locations, key=lambda x: x["matchQuality"], reverse=True)
