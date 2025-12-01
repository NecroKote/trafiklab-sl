from enum import IntEnum, StrEnum
from typing import Any, Dict, Tuple, TypeAlias

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
