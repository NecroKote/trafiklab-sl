from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin, Undefined, dataclass_json

from .common import SL_TZ, TransportMode, dt_field


class DepartureState(StrEnum):
    NOTEXPECTED = "NOTEXPECTED"
    NOTCALLED = "NOTCALLED"
    EXPECTED = "EXPECTED"
    CANCELLED = "CANCELLED"
    INHIBITED = "INHIBITED"
    ATSTOP = "ATSTOP"
    BOARDING = "BOARDING"
    BOARDINGCLOSED = "BOARDINGCLOSED"
    DEPARTED = "DEPARTED"
    PASSED = "PASSED"
    MISSED = "MISSED"
    REPLACED = "REPLACED"
    ASSUMEDDEPARTED = "ASSUMEDDEPARTED"


class JourneyState(StrEnum):
    # Do not show departure at all. Some systems might instead indicate that this departure is available only if ordered
    NOTEXPECTED = "NOTEXPECTED"

    # If a not expected dated vehicle journey is never run, it should at some point in time be considered as not run
    NOTRUN = "NOTRUN"

    # Normally show target time for departure
    EXPECTED = "EXPECTED"

    # A symbol or text indicating that the vehicle journey is not yet in progress could be added depending on presentation system configuration
    ASSIGNED = "ASSIGNED"

    # Show departure as cancelled
    CANCELLED = "CANCELLED"

    # If the presentation system only shows vehicles that are in progress, do not show the departure
    SIGNEDON = "SIGNEDON"

    # Normally show target time for departure. A symbol or text indicating that the vehicle journey is at origin, but not yet in progress could be added depending on presentation system configuration. If the presentation system only shows vehicles that are in progress, do not show the departure
    ATORIGIN = "ATORIGIN"

    # Present the current vehicle journey position, i.e. "has left station X Z minutes ago" or "currently at station Y". Systems that cannot present texts of that size should use a symbol or text indicating that the vehicle journey prediction is unreliable
    FASTPROGRESS = "FASTPROGRESS"

    # Present the current vehicle journey position, i.e. "has left station X Z minutes ago" or "currently at station Y"
    NORMALPROGRESS = "NORMALPROGRESS"

    # Present the current vehicle journey position, i.e. "has left station X Z minutes ago" or "currently at station Y" and information that "traffic moves slowly". Systems that cannot present texts of that size should use a symbol or text indicating that the vehicle journey prediction is unreliable
    SLOWPROGRESS = "SLOWPROGRESS"

    # Present the current vehicle journey position, i.e. "has left station X Z minutes ago" or "currently at station Y" and information that there is a "stop in traffic". Systems that cannot present texts of that size should use a symbol or text indicating that the vehicle journey prediction is unreliable
    NOPROGRESS = "NOPROGRESS"

    # If the vehicle system detects that a vehicle is not following the expected route, it can change the state to off route
    OFFROUTE = "OFFROUTE"

    # If the vehicle finally reaches its destination, the vehicle journey receives the state completed, else it is aborted. Once in progress, a cancellation or sign off will be regarded as the monitored vehicle journey has been aborted. If an aborted dated vehicle journey is resumed again, PubTrans will create a new instance of a monitored vehicle journey
    ABORTED = "ABORTED"

    # If the vehicle finally reaches its destination, the vehicle journey receives the state completed, else it is aborted
    COMPLETED = "COMPLETED"

    # If an expected vehicle journey is not cancelled and never becomes in progress, it should at some point in time be considered as assumed completed
    ASSUMEDCOMPLETED = "ASSUMEDCOMPLETED"


class JourneyPredictionState(StrEnum):
    NORMAL = "NORMAL"
    LOSTCONTACT = "LOSTCONTACT"
    UNRELIABLE = "UNRELIABLE"


class JourneyPassengerLevel(StrEnum):
    EMPTY = "EMPTY"
    SEATSAVAILABLE = "SEATSAVAILABLE"
    STANDINGPASSENGERS = "STANDINGPASSENGERS"
    PASSENGERSLEFTBEHIND = "PASSENGERSLEFTBEHIND"
    UNKNOWN = "UNKNOWN"


class StopAreaType(StrEnum):
    BUSTERM = "BUSTERM"
    METROSTN = "METROSTN"
    TRAMSTN = "TRAMSTN"
    RAILWSTN = "RAILWSTN"
    SHIPBER = "SHIPBER"
    FERRYBER = "FERRYBER"
    AIRPORT = "AIRPORT"
    TAXITERM = "TAXITERM"
    UNKNOWN = "UNKNOWN"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass(frozen=True)
class DepartureJourney:
    id: int
    state: JourneyState
    prediction_state: Optional[JourneyPredictionState] = None
    passenger_level: Optional[JourneyPassengerLevel] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass(frozen=True)
class StopAreaReference:
    id: int
    name: str
    sname: Optional[str] = None
    type: Optional[StopAreaType] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass(frozen=True)
class StopPointReference:
    id: int
    name: Optional[str] = None
    designation: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass(frozen=True)
class LineReference:
    id: int
    designation: Optional[str] = None
    transport_mode: Optional[TransportMode] = None
    group_of_lines: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass(frozen=True)
class DepartureDeviation:
    importance_level: int
    consequence: str
    message: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass(frozen=True)
class Departure:
    direction: str
    direction_code: int
    state: DepartureState
    display: str
    journey: DepartureJourney
    stop_area: StopAreaReference
    stop_point: StopPointReference
    line: LineReference
    deviations: List[DepartureDeviation]
    scheduled: datetime = dt_field(tzinfo=SL_TZ)
    expected: Optional[datetime] = dt_field(tzinfo=SL_TZ)
    via: Optional[str] = None
    destination: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass(frozen=True)
class DeviationScope:
    description: Optional[str] = None
    lines: Optional[List[LineReference]] = None
    stop_areas: Optional[List[StopAreaReference]] = None
    stop_points: Optional[List[StopPointReference]] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass(frozen=True)
class StopDeviation:
    id: int
    importance_level: int
    message: str
    scope: DeviationScope


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass(frozen=True)
class SiteDepartureResponse(DataClassJsonMixin):
    departures: List[Departure]
    stop_deviations: List[StopDeviation]
