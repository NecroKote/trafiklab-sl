# Trafiklab-Sl

[![version](https://img.shields.io/pypi/v/trafiklab-sl)](https://pypi.org/project/trafiklab-sl)
[![python version](https://img.shields.io/pypi/pyversions/trafiklab-sl)](https://github.com/NecroKote/trafiklab-sl)
[![test](https://github.com/NecroKote/trafiklab-sl/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/NecroKote/trafiklab-sl/actions/workflows/test.yml)
[![license](https://img.shields.io/github/license/necrokote/trafiklab-sl)](https://github.com/NecroKote/trafiklab-sl/blob/main/LICENSE.txt)

A data model describing Storstockholms Lokaltrafik (SL) data.

Also contains an async client for fetching data from the [Trafiklab API](https://www.trafiklab.se/api/).

## Installation

Install using `pip install -U trafiklab-sl`

### Development

To install the package for development, clone the repository and run:
```shell
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,test]'
```

## Usage

The client is based on the `aiohttp` library and is async. It is used to fetch data from the Trafiklab API.
The library supports following SL APIs:
- [SL Deviatons API](https://www.trafiklab.se/api/our-apis/sl/deviations/)
- [SL Transport API](https://www.trafiklab.se/api/our-apis/sl/transport/)
  - "Departures from Site"
  - "Sites"
  - "Lines"
  - "Sites"
  - "Stop Points"
- [SL Journey-planner v2 API](https://www.trafiklab.se/api/our-apis/sl/journey-planner-2/)
  - "Stop lookup"
  - "Journey Planner"
  - "System Info"
  - "Line list" (the use is discouraged, use Transport API Lines instead)

## Example

Here is an example of how to use the client to get upcoming train departures at Stockholm Central (site Id 1002).

```python
import asyncio
import aiohttp

from tsl.clients.transport import TransportClient
from tsl.clients.journey import JourneyPlannerClient, SearchLeg
from tsl.models.common import TransportMode
from tsl.utils import global_id_to_site_id
from tsl.tools.journey import SimpleJourneyInterpreter, leg_display_str


async def main():
    async with aiohttp.ClientSession() as session:

        # perform stop lookup to get the site id for Stockholm Central
        journey_client = JourneyPlannerClient(session)
        stops = await journey_client.find_stops("Stockholm Central")
        if (central_station := next(iter(stops), None)) is None:
            raise RuntimeError(r"Could not find Stockholm Central. Weird ¯\_(ツ)_/¯")

        # get the transport API site id for Stockholm Central
        transport_api_siteid = global_id_to_site_id(central_station['id'])

        # get upcoming train departures
        client = TransportClient(session)
        reponse = await client.get_site_departures(transport_api_siteid, transport=TransportMode.TRAIN)

        # get step by step journey from Stockholm Central to a specific location
        params = journey_client.build_request_params(
            origin=SearchLeg.from_stop_finder(central_station),
            destination=SearchLeg.from_coordinates("59.274695", "18.033901"),
            calc_number_of_trips=1
        )
        ways_to_get_there = await journey_client.search_trip(params)
        # use `SimpleJourneyInterpreter` to interpret the journey data in a human-readable way

    print(f"Upcoming trains at {central_station['disassembledName']}:")
    for departure in sorted(reponse["departures"], key=lambda d: d.get("expected", "")):
        print(
            f"[{departure['line'].get('designation')}] platform {departure['stop_point'].get('designation')}"
            f" to {departure.get('destination')} ({departure['display']})"
        )

    print(f"\nNumber of ways to get from Stockholm Central to 59.274695, 18.033901 - {len(ways_to_get_there)}")
    interpreter = SimpleJourneyInterpreter(ways_to_get_there[0])

    print("Itinerary of the first way:")
    for leg in interpreter.get_itinerary():
        print("  - " + leg_display_str(leg))


asyncio.run(main())
```

## Contributing

Both bug reports and pull requests are appreciated.


## Development

### pre-commit hooks

To help ensure code style and import order are consistent across the project, this project uses [pre-commit](https://pre-commit.com/) to automatically check and format code before it reaches the repository.

This project uses [pre-commit](https://pre-commit.com/) to automatically check and format code before it reaches the repository.

To set up pre-commit hooks locally:

```sh
pip install pre-commit
pre-commit install
```

After this, every time you commit, formatting tools will be run automatically on your code.

You can also run all hooks manually on all files with:

```sh
pre-commit run --all-files
```
