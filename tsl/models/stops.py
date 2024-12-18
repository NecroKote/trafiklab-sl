from dataclasses import dataclass, field
from typing import List, Optional, Union

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

        # 3BA1CDEFG -> ABCDEFG
        value.transport_siteid = int(value[2] + value[1] + value[4:])

        return value

    @classmethod
    def from_siteid(cls, value: Union[str, int]):
        """
        Create a LookupSiteId from a siteid

        `value` can be in short and long (3xx1xxxxx) form.
        """

        value = str(value).lstrip("0")

        if len(value) == 9 and value[0] == "3" and value[3] == "1":
            return cls(value)
        else:
            value = value.zfill(7)
            # ABCDEFG -> 3BA1CDEFG
            return cls(f"3{value[1]}{value[0]}1{value[2:]}")


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
