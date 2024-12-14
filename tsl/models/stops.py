from dataclasses import dataclass, field
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin, Undefined, config, dataclass_json
from marshmallow import fields


class LookupSiteId(str):
    """
    The siteid is used to identify a stop in the SL Stop Lookup API.

    It is a string of 9 characters.
    The first character is always 3.
    The 4th character is always 1.
    """

    transport_siteid: int

    def __new__(cls, value, *args, **kwargs):
        value = super().__new__(cls, value)

        if not value.isdigit():
            raise ValueError("siteid must only contain digits")

        if not (value[0] == "3" and value[3] == "1"):
            raise ValueError("siteid must start with 3 and have 1 as 4th character")

        value.transport_siteid = int(value[2] + value[1] + value[4:])

        return value


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass(frozen=True)
class Stop(DataClassJsonMixin):
    # The name of the stop generaly known to the public
    Name: str

    # Unique identifier of a stop
    SiteId: LookupSiteId = field(
        metadata=config(encoder=str, decoder=LookupSiteId, mm_field=fields.String())
    )

    # Type of the station
    Type: str

    #
    X: str

    #
    Y: str

    #
    Products: Optional[List[str]]
