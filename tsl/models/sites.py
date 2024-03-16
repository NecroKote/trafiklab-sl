from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin

from .common import SL_TZ, dt_field


@dataclass(frozen=True)
class ValidityPeriod(DataClassJsonMixin):
    """The period for which the object is valid"""

    from_: datetime = dt_field(alias="from", tzinfo=SL_TZ)
    to: Optional[datetime] = dt_field(default=None, tzinfo=SL_TZ)


@dataclass(frozen=True)
class Site(DataClassJsonMixin):
    # Unique identifier of a site
    id: int

    # Global unique site identifier
    gid: int

    # The name of the site generaly known to the public
    name: str

    # The period for which the object is valid.
    valid: ValidityPeriod

    # Alias names that describes the same place but with a different name
    alias: Optional[List[str]] = None

    # An abbreviation for the site
    abbreviation: Optional[str] = None

    # Additional note related to the site
    note: Optional[str] = None

    # WGS84 latitude in decimal degrees
    lat: Optional[float] = 0.0

    # WGS84 longitude in decimal degrees
    lon: Optional[float] = 0.0
