from enum import IntEnum, StrEnum
from typing import Any, Dict, NotRequired, Tuple, TypeAlias, TypedDict, Union

PropertiesType: TypeAlias = Dict[str, Any]
CoordTuple: TypeAlias = Tuple[float, float]


class TransportMode(StrEnum):
    BUS = "BUS"
    METRO = "METRO"
    TRAM = "TRAM"
    TRAIN = "TRAIN"
    SHIP = "SHIP"
    FERRY = "FERRY"
    TAXI = "TAXI"


class ProductClass(IntEnum):
    TRAIN = 0
    METRO = 2
    LOCAL_TRAIN = 4
    TRAM = 4
    BUS = 5
    SHIP_AND_FERRY = 9
    TRANSIT_ON_DEMAND_AREA_SERVICE = 10
    LONG_DISTANCE_TRAIN = 14
    EXPRESS_TRAIN = 14

    FOOT_PATH = 100
    FOOT_PATH_LOCAL = 99


LineId = Union[str, int]
"""
Line IDs are numeric but can be passed as int or str (e.g., 176 or "176")

Note: Express variants like "176X" are trip variants, not separate line IDs
"""

LocalDateString: TypeAlias = str
"""
The field's format is 'yyyy-MM-ddTHH:mm:ss' (ISO8601:2004)
in the local Europe/Stockholm timezone
"""

ValidityPeriod = TypedDict(
    "ValidityPeriod",
    {
        "from": LocalDateString,
        "to": NotRequired[LocalDateString],
    },
)
"""The period for which the object is valid"""
