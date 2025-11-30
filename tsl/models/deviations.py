"""
https://www.trafiklab.se/api/trafiklab-apis/sl/deviations
"""

from typing import List, Optional, TypedDict, NotRequired

from .common import TransportMode

Publish = TypedDict(
    "Publish",
    {
        "from": str,
        "upto": Optional[str],
    },
)


class Priority(TypedDict):
    importance_level: int
    influence_level: int
    urgency_level: int


class MessageVariant(TypedDict):
    header: str
    details: str
    scope_alias: str
    language: str
    weblink: NotRequired[str]


class StopPoint(TypedDict):
    id: int
    name: str


class ScopeArea(TypedDict):
    id: int
    transport_authority: int
    name: str
    type: str
    stop_points: NotRequired[List[StopPoint]]


class Line(TypedDict):
    id: int
    transport_authority: int
    transport_mode: TransportMode
    designation: NotRequired[str]
    name: NotRequired[str]
    group_of_lines: NotRequired[str]


class Scope(TypedDict):
    """Entities affected by the deviation"""

    stop_areas: NotRequired[List[ScopeArea]]
    lines: NotRequired[List[Line]]


class DeviationCategory(TypedDict):
    """Category of the deviation (e.g., FACILITY/LIFT)"""

    group: str
    type: str


class Deviation(TypedDict):
    """information regarding deviations on SLs transport network."""

    version: int
    created: str
    publish: Publish
    priority: Priority
    message_variants: List[MessageVariant]
    modified: NotRequired[str]
    deviation_case_id: NotRequired[int]
    scope: NotRequired[Scope]
    categories: NotRequired[List[DeviationCategory]]
