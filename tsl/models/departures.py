from enum import StrEnum
from typing import List, NotRequired, TypedDict

from .common import TransportMode


class DepartureState(StrEnum):
    NOT_EXPECTED = "NOTEXPECTED"
    NOT_CALLED = "NOTCALLED"
    EXPECTED = "EXPECTED"
    CANCELLED = "CANCELLED"
    INHIBITED = "INHIBITED"
    AT_STOP = "ATSTOP"
    BOARDING = "BOARDING"
    BOARDING_CLOSED = "BOARDINGCLOSED"
    DEPARTED = "DEPARTED"
    PASSED = "PASSED"
    MISSED = "MISSED"
    REPLACED = "REPLACED"
    ASSUMED_DEPARTED = "ASSUMEDDEPARTED"


class JourneyState(StrEnum):
    # Do not show departure at all. Some systems might instead indicate that this departure is available only if ordered
    NOT_EXPECTED = "NOTEXPECTED"

    # If a not expected dated vehicle journey is never run, it should at some point in time be considered as not run
    NOT_RUN = "NOTRUN"

    # Normally show target time for departure
    EXPECTED = "EXPECTED"

    # A symbol or text indicating that the vehicle journey is not yet in progress could be added depending on presentation system configuration
    ASSIGNED = "ASSIGNED"

    # Show departure as cancelled
    CANCELLED = "CANCELLED"

    # If the presentation system only shows vehicles that are in progress, do not show the departure
    SIGNED_ON = "SIGNEDON"

    # Normally show target time for departure. A symbol or text indicating that the vehicle journey is at origin, but not yet in progress could be added depending on presentation system configuration. If the presentation system only shows vehicles that are in progress, do not show the departure
    AT_ORIGIN = "ATORIGIN"

    # Present the current vehicle journey position, i.e. "has left station X Z minutes ago" or "currently at station Y". Systems that cannot present texts of that size should use a symbol or text indicating that the vehicle journey prediction is unreliable
    FAST_PROGRESS = "FASTPROGRESS"

    # Present the current vehicle journey position, i.e. "has left station X Z minutes ago" or "currently at station Y"
    NORMAL_PROGRESS = "NORMALPROGRESS"

    # Present the current vehicle journey position, i.e. "has left station X Z minutes ago" or "currently at station Y" and information that "traffic moves slowly". Systems that cannot present texts of that size should use a symbol or text indicating that the vehicle journey prediction is unreliable
    SLOW_PROGRESS = "SLOWPROGRESS"

    # Present the current vehicle journey position, i.e. "has left station X Z minutes ago" or "currently at station Y" and information that there is a "stop in traffic". Systems that cannot present texts of that size should use a symbol or text indicating that the vehicle journey prediction is unreliable
    NO_PROGRESS = "NOPROGRESS"

    # If the vehicle system detects that a vehicle is not following the expected route, it can change the state to off route
    OFF_ROUTE = "OFFROUTE"

    # If the vehicle finally reaches its destination, the vehicle journey receives the state completed, else it is aborted. Once in progress, a cancellation or sign off will be regarded as the monitored vehicle journey has been aborted. If an aborted dated vehicle journey is resumed again, PubTrans will create a new instance of a monitored vehicle journey
    ABORTED = "ABORTED"

    # If the vehicle finally reaches its destination, the vehicle journey receives the state completed, else it is aborted
    COMPLETED = "COMPLETED"

    # If an expected vehicle journey is not cancelled and never becomes in progress, it should at some point in time be considered as assumed completed
    ASSUMED_COMPLETED = "ASSUMEDCOMPLETED"


class JourneyPredictionState(StrEnum):
    NORMAL = "NORMAL"
    LOST_CONTACT = "LOSTCONTACT"
    UNRELIABLE = "UNRELIABLE"


class JourneyPassengerLevel(StrEnum):
    EMPTY = "EMPTY"
    SEATS_AVAILABLE = "SEATSAVAILABLE"
    STANDING_PASSENGERS = "STANDINGPASSENGERS"
    PASSENGERS_LEFT_BEHIND = "PASSENGERSLEFTBEHIND"
    UNKNOWN = "UNKNOWN"


class StopAreaType(StrEnum):
    BUS_TERMINAL = "BUSTERM"
    METRO_STATION = "METROSTN"
    TRAM_STATION = "TRAMSTN"
    RAILWAY_STATION = "RAILWSTN"
    SHIP_BERTH = "SHIPBER"
    FERRY_BERTH = "FERRYBER"
    AIRPORT = "AIRPORT"
    TAXI_TERMINAL = "TAXITERM"
    UNKNOWN = "UNKNOWN"


class DepartureJourney(TypedDict):
    id: int
    state: JourneyState
    prediction_state: NotRequired[JourneyPredictionState]
    passenger_level: NotRequired[JourneyPassengerLevel]


class StopAreaReference(TypedDict):
    id: int
    name: str
    sname: NotRequired[str]
    type: NotRequired[StopAreaType]


class StopPointReference(TypedDict):
    id: int
    name: NotRequired[str]
    designation: NotRequired[str]


class LineReference(TypedDict):
    id: int
    designation: NotRequired[str]
    transport_mode: NotRequired[TransportMode]
    group_of_lines: NotRequired[str]


class DepartureDeviation(TypedDict):
    importance_level: int
    consequence: str
    message: str


class Departure(TypedDict):
    direction: str
    direction_code: int
    state: DepartureState
    display: str
    journey: DepartureJourney
    stop_area: StopAreaReference
    stop_point: StopPointReference
    line: LineReference
    deviations: List[DepartureDeviation]
    scheduled: str
    expected: NotRequired[str]
    via: NotRequired[str]
    destination: NotRequired[str]


class DeviationScope(TypedDict):
    description: NotRequired[str]
    lines: NotRequired[List[LineReference]]
    stop_areas: NotRequired[List[StopAreaReference]]
    stop_points: NotRequired[List[StopPointReference]]


class StopDeviation(TypedDict):
    id: int
    importance_level: int
    message: str
    scope: DeviationScope


class SiteDepartureResponse(TypedDict):
    departures: List[Departure]
    stop_deviations: List[StopDeviation]
