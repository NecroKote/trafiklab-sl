import logging
from functools import cached_property
from typing import Any, Dict, List, NamedTuple, Tuple, Union

import aiohttp

from .. import __version__

Params = Union[List[Tuple[str, str]], Dict[str, Any], None]

PARAM_KEY = "key"
SENSITIVE_PARAMS = {PARAM_KEY}


class UrlParams(NamedTuple):
    url: str
    params: Params


class AsyncClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    @cached_property
    def user_agent(self):
        return f"{aiohttp.http.SERVER_SOFTWARE} trafiklab-sl/{__version__}"

    def _safe_params(self, params: Params) -> Params:
        if isinstance(params, dict):
            safe_params = params.copy()
        elif isinstance(params, list):
            safe_params = dict(params)
        else:
            safe_params = {}

        for key in SENSITIVE_PARAMS:
            if key in safe_params:
                safe_params[key] = "*****"

        return safe_params

    async def _request_json(self, args: UrlParams):
        self.logger.debug(
            f"Requesting {args.url} with params {self._safe_params(args.params)}"
        )
        response = await self._session.get(
            args.url,
            params=args.params,
            headers={
                "Content-Type": "application/json",
                "User-Agent": self.user_agent,
            },
        )
        response.raise_for_status()
        json = await response.json()
        return json


class ClientException(Exception):
    """Base class for client exceptions"""


class ResponseFormatChanged(ClientException):
    """Raised when the response format has changed"""


class OperationFailed(ClientException):
    """Raised when an operation failed with known error code"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")
