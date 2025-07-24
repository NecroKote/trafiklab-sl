import re
from datetime import datetime
from zoneinfo import ZoneInfo

SL_TZ = ZoneInfo("Europe/Stockholm")
ISO_MSEC_PART = re.compile(r"\.(\d{1,3})\+?")


def from_sl_dt(dt_str: str) -> datetime:
    """
    Convert a datetime string from SL format to a timezone-aware datetime object.

    The SL datetime format is expected to be in ISO 8601 format, e.g., "2023-10-01T12:00:00".
    """

    dt = datetime.fromisoformat(dt_str)
    return dt.astimezone(SL_TZ)


def global_id_to_site_id(global_id: str) -> int:
    """
    Convert a global ID to a transport site ID.

    Function assumes the global ID is in the format "909100100xxxxxxx",
    """

    if len(global_id) != 16:
        raise ValueError(
            f"Invalid global ID length: {len(global_id)}. Expected 16 characters."
        )

    prefix = "909100100"
    if not global_id.startswith(prefix):
        raise ValueError(
            f"Invalid global ID prefix: {global_id[:9]}. Expected '{prefix}'."
        )

    return int(global_id.removeprefix(prefix))
