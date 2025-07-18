from enum import IntEnum, StrEnum
from typing import TypedDict


class StopFinderResultType(StrEnum):
    ADDRESS = "address"
    STOP = "stop"
    SINGLEHOUSE = "singlehouse"
    POI = "poi"
    STREET = "street"

class StopArea(TypedDict):
    id: str
    name: str
    type: str

class StopProductClass(IntEnum):
    TRAIN = 0
    METRO = 2
    LOCAL_TRAIN = 4
    TRAM = 4
    BUS = 5
    SHIP_AND_FERRY = 9
    TRANSIT_ON_DEMAND_AREA_SERVICE = 10
    LONG_DISTANCE_TRAIN = 14
    EXPRESS_TRAIN = 14

class StopFinderType(TypedDict):
    # The id of the search result.
    id: str

    # Value is true if location is a stop.
    isGlobalId: bool

    # The name of the search result, including municipality name
    name: str

    # The name of the search result, without municipality name
    disassembledName: str

    # The coordinates of the search result.
    coord: tuple[float, float]

    # The type of the result.
    type: StopFinderResultType

    # The street name, if search result is type "street or singlehouse"
    streetName: str | None

    # The house number, if search result is "singlehouse".
    buildingNumber: str | None

    # Quality of the query matching.
    matchQuality: int

    # Products at this stop
    productClasses: list[StopProductClass]

    # Principality of the stop or stop area.
    parent: StopArea
