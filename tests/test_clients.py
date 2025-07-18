import aiohttp
import pytest

from tsl.clients.deviations import DeviationsClient
from tsl.clients.stoplookup import StopLookupClient
from tsl.clients.transport import TransportClient
from tsl.models.departures import DepartureState
from tsl.models.deviations import TransportMode


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

    assert isinstance(deviations, list)
    if deviation := next(iter(deviations), None):
        assert isinstance(deviation, dict)
        assert isinstance(deviation["version"], int)


@pytest.mark.integration
async def test_transport_departures(session):
    cl = TransportClient(session)
    response = await cl.get_site_departures(1002)

    if departure := next(iter(response["departures"]), None):
        assert departure["state"] in DepartureState



@pytest.mark.integration
async def test_transport_sites(session):
    cl = TransportClient(session)
    sites = await cl.get_sites()

    assert isinstance(sites, list)

    if site := next(iter(sites), None):
        assert isinstance(site, dict)
        assert isinstance(site["id"], int)


@pytest.mark.integration
async def test_stop_lookup(session):
    cl = StopLookupClient(session)
    stops = await cl.get_stops("Odenplan")
    assert isinstance(stops, list)

    if stops:
        assert stops[0]["disassembledName"] == "Odenplan"
        assert stops[0]["id"] == "9091001000009117"
