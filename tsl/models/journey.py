from dataclasses import dataclass
from datetime import timedelta
from enum import IntFlag, StrEnum
from typing import Any, List, NotRequired, Tuple, TypeAlias, TypedDict

from .common import CoordTuple, ProductClass, PropertiesType
from .stops import StopFinderType

DateStr: TypeAlias = str
"""Date string in format 'YYYY-MM-DD'."""

SystemValidity = TypedDict(
    "SystemValidity",
    {
        "from": DateStr,
        "to": DateStr,
    },
)
"""Route planning data availability period."""


class SearchType(StrEnum):
    # search by coordinates
    COORD = "coord"

    # search by street and stop names
    ANY = "any"


@dataclass(frozen=True)
class SearchLeg:
    type: SearchType

    value: str
    """
    location or coordinates.
    Coordinate are in format: '<x>:<y>:WGS84[dd.ddddd]'
    """

    @property
    def coordinates(self) -> Tuple[str, str]:
        """returns coordinates in format 'lat,lon'"""
        if self.type != SearchType.COORD:
            raise ValueError("SearchLeg is not of type COORD")
        coords = self.value.rsplit(":", maxsplit=1)[0]
        x, y = coords.split(":")
        return x, y

    @classmethod
    def from_coordinates(cls, lat: str, lon: str) -> "SearchLeg":
        """creates SearchLeg from coordinates"""
        return cls(SearchType.COORD, f"{lon}:{lat}:WGS84[dd.ddddd]")

    @classmethod
    def from_any(cls, value: str) -> "SearchLeg":
        """creates SearchLeg from street or stop id"""
        return cls(SearchType.ANY, value)

    @classmethod
    def from_stop_finder(cls, stop: StopFinderType) -> "SearchLeg":
        """creates SearchLeg from StopFinderType"""
        return cls(SearchType.ANY, stop["id"])


class StopFilter(IntFlag):
    """Filter for JourneyPlanner's stop finder feature."""

    STOPS = 2
    STREET = 4
    ADDRESS = 8
    POI = 32


class Language(StrEnum):
    """Supported languages for the Journey Planner API."""

    SV = "sv"  # Swedish
    EN = "en"  # English


class RouteType(StrEnum):
    LEAST_INTER_CHANGES = "leastinterchange"
    LEAST_TIME = "leasttime"
    LEAST_WALKING = "leastwalking"


class DwellTime:
    """Represents dwell time in a journey."""

    def __init__(self, duration: timedelta):
        self.duration = duration

    def to_hh_mm(self) -> str:
        """returns dwell time in format 'hh:mm'"""
        total_seconds = int(self.duration.total_seconds())
        if total_seconds >= 24 * 3600:
            raise ValueError("Dwell time cannot exceed 24 hours")

        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}"


class Manouvre(StrEnum):
    ORIGIN = "ORIGIN"
    DESTINATION = "DESTINATION"
    KEEP = "KEEP"
    TURN = "TURN"


class TurnDirection(StrEnum):
    UNKNOWN = "UNKNOWN"
    STRAIGHT = "STRAIGHT"
    SHARP_LEFT = "SHARP_LEFT"
    RIGHT = "RIGHT"
    LEFT = "LEFT"


class LegPoint(TypedDict):
    coord: CoordTuple
    cumDistance: int
    cumDuration: int
    distance: int
    duration: int
    fromCoordsIndex: int
    manouvre: Manouvre
    properties: NotRequired[PropertiesType]
    name: str
    skyDirection: NotRequired[int]
    toCoordsIndex: int
    turnDirection: TurnDirection


class JourneyOrigin(StopFinderType):
    departureTimeBaseTimetable: NotRequired[str]
    departureTimePlanned: NotRequired[str]
    departureTimeEstimated: NotRequired[str]
    properties: NotRequired[PropertiesType]


class JourneyDestination(StopFinderType):
    arrivalTimeBaseTimetable: NotRequired[str]
    arrivalTimePlanned: NotRequired[str]
    arrivalTimeEstimated: NotRequired[str]
    properties: NotRequired[PropertiesType]


class JourneyStop(StopFinderType):
    departureTimePlanned: NotRequired[str]
    arrivalTimePlanned: NotRequired[str]


TransportationProduct = TypedDict(
    "TransportationProduct",
    {"id": NotRequired[int], "class": ProductClass, "name": str, "iconId": int},
)


class TransportationOperator(TypedDict):
    id: str
    name: str


class TransportationDestination(TypedDict):
    id: str
    name: str
    type: str


class JourneyTransportation(TypedDict):
    id: NotRequired[str]
    name: NotRequired[str]
    disassembledName: NotRequired[str]
    number: NotRequired[str]
    product: TransportationProduct
    operator: NotRequired[TransportationOperator]
    destination: NotRequired[TransportationDestination]
    properties: PropertiesType


class FootPathLeg(TypedDict):
    duration: int
    footPathElem: List[Any]
    position: str


class JoyrneyLeg(TypedDict):
    infos: List[Any]
    distance: NotRequired[int]
    duration: int
    footPathInfo: NotRequired[List[FootPathLeg]]
    pathDescriptions: NotRequired[List[LegPoint]]
    origin: JourneyOrigin
    destination: JourneyDestination
    transportation: JourneyTransportation
    stopSequence: List[JourneyStop]
    properties: PropertiesType
    coords: NotRequired[List[CoordTuple]]
    realtimeStatus: NotRequired[List[str]]
    isRealtimeControlled: NotRequired[bool]


class DaysOfService(TypedDict):
    rvb: str


class Journey(TypedDict):
    tripDuration: int
    tripRtDuration: int
    rating: int
    isAdditional: bool
    interchanges: int
    legs: List[JoyrneyLeg]
    daysOfService: DaysOfService
