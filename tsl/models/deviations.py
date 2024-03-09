"""
https://www.trafiklab.se/api/trafiklab-apis/sl/deviations
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin

from .common import SL_TZ, TransportMode, dt_field


@dataclass(frozen=True)
class Publish(DataClassJsonMixin):
    from_: datetime = dt_field(alias="from", tzinfo=SL_TZ)
    upto: Optional[datetime] = dt_field(default=None, tzinfo=SL_TZ)


@dataclass(frozen=True)
class Priority(DataClassJsonMixin):
    importance_level: int
    influence_level: int
    urgency_level: int


@dataclass(frozen=True)
class MessageVariant(DataClassJsonMixin):
    header: str
    details: str
    scope_alias: str
    language: str
    weblink: Optional[str] = None


@dataclass(frozen=True)
class StopPoint(DataClassJsonMixin):
    id: int
    name: str


@dataclass(frozen=True)
class ScopeArea(DataClassJsonMixin):
    id: int
    transport_authority: int
    name: str
    type: str
    stop_points: Optional[List[StopPoint]] = None


@dataclass(frozen=True)
class Line(DataClassJsonMixin):
    id: int
    transport_authority: int
    transport_mode: TransportMode
    designation: Optional[str] = None
    name: Optional[str] = None
    group_of_lines: Optional[str] = None


@dataclass(frozen=True)
class Scope(DataClassJsonMixin):
    """Entities affected by the deviation"""

    stop_areas: Optional[List[ScopeArea]] = None
    lines: Optional[List[Line]] = None


@dataclass(frozen=True)
class Deviation(DataClassJsonMixin):
    """information regarding deviations on SLs transport network."""

    version: int
    created: datetime = dt_field(tzinfo=SL_TZ)
    publish: Publish
    priority: Priority
    message_variants: List[MessageVariant]
    modified: Optional[datetime] = dt_field(default=None, tzinfo=SL_TZ)
    deviation_case_id: Optional[int] = None
    scope: Optional[Scope] = None
