from typing import List, Optional, Union, cast

from ..models.deviations import Deviation, TransportMode
from .common import AsyncClient, UrlParams

__all__ = ("DeviationsClient",)

# Line IDs are numeric but can be passed as int or str (e.g., 176 or "176")
# Note: Express variants like "176X" are trip variants, not separate line IDs
LineId = Union[str, int]


class DeviationsClient(AsyncClient):
    """
    client for SL Deviations API
    https://www.trafiklab.se/api/trafiklab-apis/sl/deviations/#/
    """

    @staticmethod
    def get_request_url_params(
        future: Optional[bool] = None,
        site: Optional[List[int]] = None,
        line: Optional[List[LineId]] = None,
        transport_authority: Optional[int] = None,
        transport_mode: Optional[List[TransportMode]] = None,
    ) -> UrlParams:
        """
        Build URL parameters for deviations request.

        Args:
            future: Include future deviations (default: False)
            site: Filter by site IDs (4-7 digit integers)
            line: Filter by line IDs (e.g., 10, 43, "176")
            transport_authority: Filter by transport authority ID
            transport_mode: Filter by transport modes (BUS, METRO, TRAM, TRAIN, SHIP, FERRY, TAXI)

        Returns:
            UrlParams ready for request
        """
        params: List[tuple[str, str]] = []
        if future is not None:
            params.append(("future", "true" if future else "false"))
        if site is not None:
            params.extend(("site", str(x)) for x in site)
        if line is not None:
            params.extend(("line", str(x)) for x in line)
        if transport_authority is not None:
            params.append(("transport_authority", str(transport_authority)))
        if transport_mode is not None:
            params.extend(("transport_mode", x.value) for x in transport_mode)

        return UrlParams("https://deviations.integration.sl.se/v1/messages", params)

    async def get_deviations(
        self,
        future: Optional[bool] = None,
        site: Optional[List[int]] = None,
        line: Optional[List[LineId]] = None,
        transport_authority: Optional[int] = None,
        transport_mode: Optional[List[TransportMode]] = None,
    ) -> List[Deviation]:
        """
        Get active or future deviation messages.

        Args:
            future: Include future deviations (default: False)
            site: Filter by site IDs (4-7 digit integers)
            line: Filter by line IDs (e.g., 10, 43, "176")
            transport_authority: Filter by transport authority ID (e.g., 1 for SL)
            transport_mode: Filter by transport modes

        Returns:
            List of Deviation objects containing:
            - version, created, modified timestamps
            - deviation_case_id
            - publish period (from/upto)
            - priority (importance, influence, urgency levels)
            - message_variants (header, details, language, weblink)
            - scope (affected stop_areas and lines)
            - categories (e.g., FACILITY/LIFT)
        """
        args = self.get_request_url_params(
            future, site, line, transport_authority, transport_mode
        )
        response = await self._request_json(args)
        return cast(List[Deviation], response)
