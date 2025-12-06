from typing import List, NotRequired, TypedDict

from .common import ValidityPeriod


class Site(TypedDict):
    id: int
    """Unique identifier of a site"""

    gid: int
    """Global unique site identifier"""

    name: str
    """The name of the site generaly known to the public"""

    alias: NotRequired[List[str]]
    """Alias names that describes the same place but with a different name"""

    abbreviation: NotRequired[str]
    """An abbreviation for the site"""

    note: NotRequired[str]
    """Additional note related to the site"""

    lat: NotRequired[float]
    """WGS84 latitude in decimal degrees"""

    lon: NotRequired[float]
    """WGS84 longitude in decimal degrees"""

    valid: ValidityPeriod
    """The period for which the object is valid."""
