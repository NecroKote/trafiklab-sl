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
- [SL Journey-planner v2 API](https://www.trafiklab.se/api/our-apis/sl/journey-planner-2/)
  - "Stop lookup"

More APIs will be added in the future.

## Example

Here is an example of how to use the client to get upcoming train departures at Stockholm Central (site Id 1002).

```python
import asyncio
import aiohttp

from tsl.clients.stoplookup import StopLookupClient
from tsl.clients.transport import TransportClient
from tsl.models.common import TransportMode
from tsl.utils import global_id_to_site_id


async def main():
    async with aiohttp.ClientSession() as session:

        # perform stop lookup to get the site id for Stockholm Central
        lookup_client = StopLookupClient(session)
        stops = await lookup_client.get_stops("Stockholm Central")
        if (central_station := next(iter(stops), None)) is None:
            raise RuntimeError(r"Could not find Stockholm Central. Weird ¯\_(ツ)_/¯")

        # get the transport API site id for Stockholm Central
        transport_api_siteid = global_id_to_site_id(central_station['id'])

        # get upcoming train departures
        client = TransportClient(session)
        reponse = await client.get_site_departures(transport_api_siteid, transport=TransportMode.TRAIN)

    print(f"Upcoming trains at {central_station['disassembledName']}:")
    for departure in sorted(reponse["departures"], key=lambda d: d.get("expected", "")):
        print(
            f"[{departure['line'].get('designation')}] platform {departure['stop_point'].get('designation')}"
            f" to {departure.get('destination')} ({departure['display']})"
        )


asyncio.run(main())
```

## Contributing

Both bug reports and pull requests are appreciated.
