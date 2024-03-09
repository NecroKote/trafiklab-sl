from dataclasses import MISSING, field
from datetime import datetime
from enum import StrEnum
from typing import Optional

from dataclasses_json import config


def dt_field(alias: Optional[str] = None, default=MISSING):
    """wrap `datetime` field with this so that `dataclasses_json` uses correct format"""

    def _dt_from_str_or_ts(v: str | float):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        else:
            return datetime.fromtimestamp(v)

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
