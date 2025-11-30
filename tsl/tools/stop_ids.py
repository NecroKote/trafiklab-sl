"""
Utility for converting between different SL stop ID formats.

Different SL APIs use different ID formats for the same stops:

1. Transport API site ID (4-5 digits):
   - Example: 9001 (T-Centralen), 9117 (Odenplan)
   - Used in: TransportClient.get_site_departures(site_id=9001)

2. Journey Planner global ID (16 digits):
   - Example: 9091001000009001 (T-Centralen)
   - Format: "909100100000" + site_id (zero-padded to 4 digits)
   - Used in: SearchLeg value for journey planning
   - Returned by: JourneyPlannerClient.find_stops()

3. Journey Planner stopId (8 digits):
   - Example: 18009001 (T-Centralen)
   - Format: "1800" + site_id (zero-padded to 4 digits)
   - Found in: StopLocation.properties.stopId from find_stops()

This module provides conversion functions between these formats.

Example workflow:
    # 1. Search for stops using Journey Planner
    stops = await journey_client.find_stops("odenplan")
    global_id = stops[0]["id"]  # "9091001000009117"

    # 2. Convert to Transport API site_id for departures
    site_id = global_id_to_site_id(global_id)  # 9117
    departures = await transport_client.get_site_departures(site_id)
"""

__all__ = (
    "site_id_to_global_id",
    "global_id_to_site_id",
    "site_id_to_stop_id",
    "stop_id_to_site_id",
    "global_id_to_stop_id",
    "stop_id_to_global_id",
)

# Prefix for Journey Planner global IDs (SL region)
GLOBAL_ID_PREFIX = "909100100000"

# Prefix for Journey Planner stopId format
STOP_ID_PREFIX = "1800"


def site_id_to_global_id(site_id: int) -> str:
    """
    Convert Transport API site ID to Journey Planner global ID.

    Args:
        site_id: Transport API site ID (e.g., 9001)

    Returns:
        Journey Planner global ID (e.g., "9091001000009001")

    Example:
        >>> site_id_to_global_id(9001)
        '9091001000009001'
    """
    return f"{GLOBAL_ID_PREFIX}{site_id:04d}"


def global_id_to_site_id(global_id: str) -> int:
    """
    Extract Transport API site ID from Journey Planner global ID.

    Args:
        global_id: Journey Planner global ID (e.g., "9091001000009001")

    Returns:
        Transport API site ID (e.g., 9001)

    Example:
        >>> global_id_to_site_id("9091001000009001")
        9001
    """
    if not global_id.startswith(GLOBAL_ID_PREFIX):
        raise ValueError(
            f"Invalid global ID format: {global_id}. "
            f"Expected prefix {GLOBAL_ID_PREFIX}"
        )
    return int(global_id[len(GLOBAL_ID_PREFIX) :])


def site_id_to_stop_id(site_id: int) -> str:
    """
    Convert Transport API site ID to Journey Planner stopId format.

    Args:
        site_id: Transport API site ID (e.g., 9001)

    Returns:
        Journey Planner stopId (e.g., "18009001")

    Example:
        >>> site_id_to_stop_id(9001)
        '18009001'
    """
    return f"{STOP_ID_PREFIX}{site_id:04d}"


def stop_id_to_site_id(stop_id: str) -> int:
    """
    Extract Transport API site ID from Journey Planner stopId format.

    Args:
        stop_id: Journey Planner stopId (e.g., "18009001")

    Returns:
        Transport API site ID (e.g., 9001)

    Example:
        >>> stop_id_to_site_id("18009001")
        9001
    """
    if not stop_id.startswith(STOP_ID_PREFIX):
        raise ValueError(
            f"Invalid stopId format: {stop_id}. "
            f"Expected prefix {STOP_ID_PREFIX}"
        )
    return int(stop_id[len(STOP_ID_PREFIX) :])


def global_id_to_stop_id(global_id: str) -> str:
    """
    Convert Journey Planner global ID to stopId format.

    Args:
        global_id: Journey Planner global ID (e.g., "9091001000009001")

    Returns:
        Journey Planner stopId (e.g., "18009001")
    """
    site_id = global_id_to_site_id(global_id)
    return site_id_to_stop_id(site_id)


def stop_id_to_global_id(stop_id: str) -> str:
    """
    Convert Journey Planner stopId format to global ID.

    Args:
        stop_id: Journey Planner stopId (e.g., "18009001")

    Returns:
        Journey Planner global ID (e.g., "9091001000009001")
    """
    site_id = stop_id_to_site_id(stop_id)
    return site_id_to_global_id(site_id)
