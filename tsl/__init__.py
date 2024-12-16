from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

try:
    if TYPE_CHECKING:
        assert __package__

    __version__ = version(__package__)
except PackageNotFoundError:
    __version__ = "0.0.0+local"
