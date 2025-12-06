# Line IDs are numeric but can be passed as int or str (e.g., 176 or "176")
from enum import StrEnum
from typing import List, NotRequired, TypedDict

from .common import TransportMode, ValidityPeriod


class TransportAuthorityReference(TypedDict):
    """Transport authority reference."""

    id: int
    """Unique identifier of a transport authority"""

    name: str
    """Name of the the transport authority"""


class TransportAuthority(TypedDict):
    """Full transport authority information."""

    id: int
    """Unique identifier of a transport authority"""

    gid: int
    """Global unique identification number that identifies the transport authority"""

    name: str
    """Name of the the transport authority"""

    formal_name: NotRequired[str]

    code: str

    street: NotRequired[str]
    postal_code: NotRequired[int]
    city: NotRequired[str]
    country: NotRequired[str]

    valid: ValidityPeriod
    """The period for which the object is valid."""


class ContractorReference(TypedDict):
    """Line contractor information."""

    id: int
    """Unique identifikation number that identifies a contractor within Region Stockholm"""

    name: str
    """Name of the contractor"""


class Line(TypedDict):
    """Line information from the lines endpoint."""

    id: int
    """Unique identifier of a line within a transport authority"""

    gid: int
    """Global unique identifier of a line"""

    name: str
    """Line name generally known to the public"""

    designation: NotRequired[str]
    """Additional identifier for the line for example number for trains"""

    transport_mode: NotRequired[TransportMode]
    """Transport mode for a line"""

    group_of_lines: NotRequired[str]
    """Name used to group lines"""

    transport_authority: NotRequired[TransportAuthorityReference]

    contractor: NotRequired[ContractorReference]

    valid: ValidityPeriod


class LinesResponse(TypedDict):
    """Response from /lines endpoint, grouped by transport mode."""

    metro: List[Line]
    """List of lines for metro"""

    tram: List[Line]
    """List of lines for tram"""

    train: List[Line]
    """List of lines for train"""

    bus: List[Line]
    """List of lines for buses"""

    ship: List[Line]
    """List of lines for ship"""

    ferry: List[Line]
    """List of lines for ferry"""

    taxi: List[Line]
    """List of lines for taxi"""


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


class StopAreaReference(TypedDict):
    """Stop area information."""

    id: int
    """Unique identifier of a stop area (In journey endpoint, 0 means no stop area found)"""

    name: str
    """Name of a stop area (In journey endpoint, UNKNOWN is returned the field is blank)"""

    sname: NotRequired[str]
    """Short name of a stop area"""

    type: NotRequired[StopAreaType]
    """Describes the type of stop area"""


class StopPointType(StrEnum):
    PLATFORM = "PLATFORM"
    BUSSTOP = "BUSSTOP"
    ENTRANCE = "ENTRANCE"
    EXIT = "EXIT"
    GATE = "GATE"
    REFUGE = "REFUGE"
    PIER = "PIER"
    TRACK = "TRACK"
    UNKNOWN = "UNKNOWN"


class StopPoint(TypedDict):
    """Stop point information from the stop-points endpoint."""

    id: int
    """Unique identifier of a stop point"""

    gid: int
    """Global unique identifier of a stop point"""

    pattern_point_gid: int
    """Global unique identifier of a pattern point"""

    name: NotRequired[str]
    """Name of a stop point (In journey endpoint, UNKNOWN is returned the field is blank)"""

    sname: NotRequired[str]
    """Short name"""

    designation: NotRequired[str]
    """Designation of a stop point"""

    local_num: int
    """The local number of the stop point"""

    type: StopPointType
    """Describes the type of stop point"""

    has_entrance: bool
    """You have to pass an entrance to get to the stop point"""

    lat: NotRequired[float]
    """WGS84 latitude in decimal degrees"""

    lon: NotRequired[float]
    """WGS84 longitude in decimal degrees"""

    door_orientation: NotRequired[float]
    """The orientation of the door at the stop point. 0 - 360 """

    transport_authority: TransportAuthorityReference

    stop_area: NotRequired[StopAreaReference]

    valid: ValidityPeriod
    """The period for which the object is valid."""
