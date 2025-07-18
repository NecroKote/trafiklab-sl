from typing import List, TypedDict, NotRequired

ValidityPeriod = TypedDict(
    "ValidityPeriod",
    {
        "from": str,
        "to": NotRequired[str],
    },
)
"""The period for which the object is valid"""


class Site(TypedDict):
    # Unique identifier of a site
    id: int

    # Global unique site identifier
    gid: int

    # The name of the site generaly known to the public
    name: str

    # The period for which the object is valid.
    valid: ValidityPeriod

    # Alias names that describes the same place but with a different name
    alias: NotRequired[List[str]]

    # An abbreviation for the site
    abbreviation: NotRequired[str]

    # Additional note related to the site
    note: NotRequired[str]

    # WGS84 latitude in decimal degrees
    lat: NotRequired[float]

    # WGS84 longitude in decimal degrees
    lon: NotRequired[float]
