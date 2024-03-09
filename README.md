# Trafiklab-Sl

[![version](https://img.shields.io/pypi/v/trafiklab-sl)](https://pypi.org/project/trafiklab-sl)
[![python version](https://img.shields.io/pypi/pyversions/trafiklab-sl)](https://github.com/NecroKote/trafiklab-sl)
[![license](https://img.shields.io/github/license/necrokote/trafiklab-sl)](https://github.com/NecroKote/trafiklab-sl/blob/main/LICENSE.txt)

A data model for Storstockholms Lokaltrafik (SL) data.

Also contains an async client for fetching data from the [Trafiklab API](https://www.trafiklab.se/api/).

## Installation

Install using `pip install -U trafiklab-sl`

### Development

To install the package for development, clone the repository and run:
```shell
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Usage

The client is based on the `aiohttp` library and is async. It is used to fetch data from the Trafiklab API.
The library supports two SL APIs:
- [SL Deviatons API](https://www.trafiklab.se/api/trafiklab-apis/sl/deviations/)
- [SL Transport API](https://www.trafiklab.se/api/trafiklab-apis/sl/transport/) - just "Departures from Site" for now

More APIs will be added in the future.

## Example

Here is an example of how to use the client to get upcoming train departures at Stockholm Central (site Id 1002).

```python
import asyncio

from tsl.clients.transport import TransportClient
from tsl.models.common import TransportMode


async def main():
    client = TransportClient()
    reponse = await client.get_site_departures(1002, transport=TransportMode.TRAIN)

    print("Upcoming trains at Stockholm Central:")
    for departure in sorted(reponse.departures, key=lambda d: d.expected):
        print(
            f"[{departure.line.designation}] platform {departure.stop_point.designation}"
            f" to {departure.destination} ({departure.display})"
        )


asyncio.run(main())
```

## Contributing

Both bug reports and pull requests are appreciated.
