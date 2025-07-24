from enum import StrEnum
from typing import List, TypedDict, NotRequired

from .common import CoordTuple, ProductClass


class StopFinderResultType(StrEnum):
    ADDRESS = "address"
    STOP = "stop"
    PLATFORM = "platform"
    SINGLEHOUSE = "singlehouse"
    POI = "poi"
    STREET = "street"


class StopArea(TypedDict):
    id: str
    name: str
    type: str


class StopFinderType(TypedDict):
    # The id of the search result.
    id: str

    # Value is true if location is a stop.
    isGlobalId: NotRequired[bool]

    # The name of the search result, including municipality name
    name: str

    # The name of the search result, without municipality name
    disassembledName: str

    # The coordinates of the search result.
    coord: CoordTuple

    # The type of the result.
    type: StopFinderResultType

    # The street name, if search result is type "street or singlehouse"
    streetName: NotRequired[str]

    # The house number, if search result is "singlehouse".
    buildingNumber: NotRequired[str]

    # Quality of the query matching.
    matchQuality: int

    # Products at this stop
    productClasses: NotRequired[List[ProductClass]]

    # Principality of the stop or stop area.
    parent: StopArea
