import pytest

from tsl.clients.deviations import DeviationsClient
from tsl.clients.transport import TransportClient
from tsl.models.departures import Departure, SiteDepartureResponse
from tsl.models.deviations import Deviation, TransportMode


@pytest.mark.integration
async def test_deviations():
    cl = DeviationsClient()
    deviations = await cl.get_deviations(
        line=["10", "43"],
        transport_mode=[TransportMode.METRO, TransportMode.TRAIN],
    )

    # serialization loop
    raw = Deviation.schema().dumps(deviations, many=True)
    Deviation.schema().loads(raw, many=True)


@pytest.mark.integration
async def test_transport_departures():
    cl = TransportClient()
    response = await cl.get_site_departures(1002)

    assert isinstance(response, SiteDepartureResponse)

    if response.departures:
        assert isinstance(response.departures[0], Departure)

    # serialization loop
    raw = SiteDepartureResponse.schema().dumps(response)
    SiteDepartureResponse.schema().loads(raw)
