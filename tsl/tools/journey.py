from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Generator, Protocol, TypeVar

from tsl.models.journey import Journey, ProductClass
from tsl.models.stops import StopFinderResultType, StopFinderType

K = TypeVar("K")


def first_not_none(*args: K | None, default: K = None) -> K:
    """
    Returns the first non-None value from the given arguments.
    If no non-None value is found, returns None.
    """
    for arg in args:
        if arg is not None:
            return arg

    if default is None:
        raise ValueError("No non-None value found")

    return default


class JourneyLeg(Protocol):
    _type: str
    _from: StopFinderType
    _to: StopFinderType
    duration: timedelta
    distance: int | None = None


@dataclass
class Walk(JourneyLeg):
    _from: StopFinderType
    _to: StopFinderType
    duration: timedelta

    distance: int

    _type: str = "walk"

    def __str__(self) -> Any:
        distance_str = f"{self.distance}m, " if self.distance else ""
        return f"Walk from {self._from} to {self._to} ({distance_str}{self.duration})"


@dataclass
class Ride(JourneyLeg):
    _from: StopFinderType
    _to: StopFinderType
    duration: timedelta

    on: str
    stops: int

    _type: str = "ride"

    def __str__(self) -> Any:
        return f"Ride {self.on} from {self._from} to {self._to} ({self.stops} stops, {self.duration})"


def pretty_duration(td: timedelta) -> str:
    """Returns a human-readable string representation of a timedelta."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    approx = False

    parts = []
    if hours > 0:
        return str(td)

    if seconds > 0:
        approx = True

    if minutes > 0:
        parts.append(f"{minutes} min")

    if not parts:
        parts.append("1 min")

    return ("~" if approx else "") + " ".join(parts)


def location_display_str(obj: StopFinderType, with_parent: bool = False) -> str:
    """Returns a human-readable string representation of a stop finder result."""

    def _platform() -> str:
        suffix = "platform"
        products = obj.get("productClasses", [])

        if products == [ProductClass.METRO]:
            suffix = "metro platform"
        elif products == [ProductClass.TRAIN]:
            suffix = "train platform"
        elif products == [ProductClass.BUS]:
            suffix = "bus stop"

        if with_parent:
            parent_name = obj["parent"].get("disassembledName", obj["parent"]["name"])
            if parent_name != obj["disassembledName"]:
                return f"{suffix} {obj['disassembledName']} on {parent_name}"

        return f"{suffix} {obj['disassembledName']}"

    def _name() -> str:
        return f"{obj['name']}"

    to_str = {
        StopFinderResultType.STOP: lambda: f"{obj['disassembledName']} stop",
        StopFinderResultType.PLATFORM: _platform,
    }.get(obj["type"], _name)

    return to_str()


def leg_display_str(leg: JourneyLeg) -> str:
    """Returns a human-readable string representation of a journey leg."""

    action = leg._type.capitalize()
    from_str = location_display_str(leg._from)
    to_str = location_display_str(leg._to, with_parent=True)

    from_platfrom = leg._from["type"] == StopFinderResultType.PLATFORM
    to_platform = leg._to["type"] == StopFinderResultType.PLATFORM

    # changing platforms on the same station
    if (
        from_platfrom
        and to_platform
        and leg._from["parent"]["id"] == leg._to["parent"]["id"]
    ):
        action = "Change platform"

    if distance := (leg.distance or 0):
        action += f" {distance} m"

    if isinstance(leg, Ride):
        action += f" on {leg.on}"

    return f"{action} from {from_str} to {to_str} ({pretty_duration(leg.duration)})"


class SimpleJourneyInterpreter:
    """Simple interpreter for journey data."""

    def __init__(self, raw_data: Journey):
        self.raw_data = raw_data

    @property
    def duration(self) -> timedelta:
        """Returns the total duration of the journey in a human-readable format."""
        return timedelta(seconds=self.raw_data["tripDuration"])

    @property
    def rt_duration(self) -> timedelta:
        """Returns the real-time duration of the journey in a human-readable format."""
        return timedelta(seconds=self.raw_data["tripRtDuration"])

    def get_itinerary(self) -> Generator[JourneyLeg, None, None]:
        """Returns a simplified itinerary of the journey."""

        on_foot = {ProductClass.FOOT_PATH, ProductClass.FOOT_PATH_LOCAL}

        for leg in self.raw_data["legs"]:
            transport = leg["transportation"]
            if transport["product"]["class"] in on_foot:
                yield Walk(
                    _from=leg["origin"],
                    _to=leg["destination"],
                    duration=timedelta(seconds=leg["duration"]),
                    distance=leg.get("distance", 0),
                )
            else:
                yield Ride(
                    _from=leg["origin"],
                    _to=leg["destination"],
                    duration=timedelta(seconds=leg["duration"]),
                    on=first_not_none(
                        transport.get("number"),
                        (
                            f"{transport['product']['name']} {transport.get('disassembledName')}"
                            if transport.get("disassembledName")
                            else None
                        ),
                        default="",
                    ),
                    stops=len(leg["stopSequence"]),
                )
