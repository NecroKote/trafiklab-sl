from typing import List

try:
    from warnings import deprecated
except ImportError:
    from typing_extensions import deprecated

from ..models.journey import SearchLeg, StopFilter
from ..models.stops import StopFinderType
from .journey import JourneyPlannerClient


@deprecated("Use JourneyPlannerClient.find_stops() instead")
class StopLookupClient(JourneyPlannerClient):
    """
    client for SL Stop Lookup API
    https://www.trafiklab.se/sv/api/our-apis/sl/journey-planner-2/
    """

    async def get_stops(self, search_string: str) -> List[StopFinderType]:
        """
        Get stops by search string
        """

        return await self.find_stops(
            SearchLeg.from_any(search_string), StopFilter.STOPS
        )

    async def get_address(self, search_string: str) -> List[StopFinderType]:
        """
        Get street or address by search string
        """

        return await self.find_stops(
            SearchLeg.from_any(search_string),
            StopFilter.STREET | StopFilter.ADDRESS,
        )
