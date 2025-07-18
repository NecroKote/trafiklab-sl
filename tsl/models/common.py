import re
import sys
from dataclasses import MISSING, field
from datetime import datetime
from enum import StrEnum
from typing import Optional, Union
from zoneinfo import ZoneInfo

from dataclasses_json import config

ISO_MSEC_PART = re.compile(r"\.(\d{1,3})\+?")
SL_TZ = ZoneInfo("Europe/Stockholm")


def dt_field(alias: Optional[str] = None, default=MISSING, tzinfo=None):
    """wrap `datetime` field with this so that `dataclasses_json` uses correct format"""

    def _dt_from_str_or_ts(v: Union[str, float]):
        if isinstance(v, str):
            # HACK: python prior to 3.11 does not handle ms part correctly
            # in fromisoformat unless it's 3 digits long
            if sys.version_info < (3, 11):
                if msec := ISO_MSEC_PART.search(v):
                    if len(msec.group(1)) < 3:
                        v = v.replace(msec.group(0), f".{msec.group(1).ljust(3, '0')}+")

            dt = datetime.fromisoformat(v)
        else:
            dt = datetime.fromtimestamp(v)

        # make sure that tzinfo is set if it's not None
        if dt.tzinfo is None and tzinfo is not None:
            dt = dt.replace(tzinfo=tzinfo)

        return dt

    return field(
        default=default,
        metadata=config(
            field_name=alias,
            encoder=datetime.isoformat,
            decoder=_dt_from_str_or_ts,
        ),
    )


class TransportMode(StrEnum):
    BUS = "BUS"
    METRO = "METRO"
    TRAM = "TRAM"
    TRAIN = "TRAIN"
    SHIP = "SHIP"
    FETTRY = "FETTRY"
    TAXI = "TAXI"
