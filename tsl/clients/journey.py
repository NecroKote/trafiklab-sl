from typing import List

from tsl.models.journey import DwellTime, Journey, Language, RouteType, SearchLeg

from .common import AsyncClient, OperationFailed, ResponseFormatChanged, UrlParams


class JourneyPlannerClient(AsyncClient):
    """
    client for SL Journey Planner v2 API
    https://www.trafiklab.se/sv/api/our-apis/sl/journey-planner-2/
    """

    @staticmethod
    def build_request_params(
        origin: SearchLeg,
        destination: SearchLeg,
        calc_number_of_trips: int = 1,
        via: SearchLeg | None = None,
        not_via: SearchLeg | None = None,
        dwell_time: DwellTime | None = None,
        language: Language | None = None,
        max_changes: int | None = None,
        route_type: RouteType | None = None,
        include_coordinates: bool | None = None,
    ) -> UrlParams:
        """returns url and params to request journey planner API"""

        if calc_number_of_trips > 3 or calc_number_of_trips < 1:
            raise ValueError("calc_number_of_trips must be between 1 and 3")

        params = [
            ("type_origin", origin.type),
            ("name_origin", origin.value),
            ("type_destination", destination.type),
            ("name_destination", destination.value),
            ("calc_number_of_trips", calc_number_of_trips),
        ]

        if via is not None:
            params.append(("type_via", via.type))
            params.append(("name_via", via.value))

        if not_via is not None:
            params.append(("type_not_via", not_via.type))
            params.append(("name_not_via", not_via.value))

        if dwell_time is not None:
            params.append(("dwell_time", dwell_time.to_hh_mm()))

        if language is not None:
            params.append(("language", language))

        if max_changes is not None:
            params.append(("max_changes", max_changes))

        if route_type is not None:
            params.append(("route_type", route_type.value))

        if include_coordinates is not None:
            params.append(("gen_c", "true" if include_coordinates else "false"))

        return UrlParams(
            "https://journeyplanner.integration.sl.se/v2/trips",
            params,
        )

    async def search_trip(self, params: UrlParams) -> List[Journey]:
        response = await self._request_json(params)

        if (journeys := response.get("journeys")) is None:
            if messages := response.get("systemMessages"):
                filtered_errors = [
                    x["text"]
                    for x in messages
                    if x["type"] == "error" and x["code"] != -8010
                ]
                raise OperationFailed(filtered_errors)

            raise ResponseFormatChanged(
                "Response format has changed, expected 'journeys' or `systemMessages` keys in response"
            )

        return journeys
