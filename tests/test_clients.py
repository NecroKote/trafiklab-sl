import os

import aiohttp
import pytest

from tsl.clients.deviations import DeviationsClient
from tsl.clients.stoplookup import StopLookupClient
from tsl.clients.transport import TransportClient
from tsl.models.departures import Departure, SiteDepartureResponse
from tsl.models.deviations import Deviation, TransportMode
from tsl.models.sites import Site
from tsl.models.stops import Stop


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.mark.integration
async def test_deviations(session):
    cl = DeviationsClient(session)
    deviations = await cl.get_deviations(
        line=["10", "43"],
        transport_mode=[TransportMode.METRO, TransportMode.TRAIN],
    )

    # serialization loop
    raw = Deviation.schema().dumps(deviations, many=True)
    # ... with extra data to be ignored
    raw = raw[:-2] + ', "extra": "data"}]'
    Deviation.schema().loads(raw, many=True)


@pytest.mark.integration
async def test_transport_departures(session):
    cl = TransportClient(session)
    response = await cl.get_site_departures(1002)

    assert isinstance(response, SiteDepartureResponse)

    if response.departures:
        assert isinstance(response.departures[0], Departure)

    # serialization loop
    raw = SiteDepartureResponse.schema().dumps(response)
    # ... with extra data to be ignored
    raw = raw[:-1] + ', "extra": "data"}'
    SiteDepartureResponse.schema().loads(raw)


@pytest.mark.integration
async def test_transport_sites(session):
    cl = TransportClient(session)
    sites = await cl.get_sites()

    # serialization loop
    raw = Site.schema().dumps(sites, many=True)
    # ... with extra data to be ignored
    raw = raw[:-2] + ', "extra": "data"}]'
    Site.schema().loads(raw, many=True)


@pytest.mark.integration
async def test_stop_lookup(session):
    cl = StopLookupClient(os.environ["SL_LOOKUP_API_KEY"], session)
    stops = await cl.get_stops("Oden")

    # serialization loop
    raw = Stop.schema().dumps(stops, many=True)
    # ... with extra data to be ignored
    raw = raw[:-2] + ', "extra": "data"}]'
    Stop.schema().loads(raw, many=True)
