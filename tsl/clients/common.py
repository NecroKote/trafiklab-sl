from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union

import aiohttp

SessionFactory = Callable[[], aiohttp.ClientSession]


class UrlParams(NamedTuple):
    url: str
    params: Union[List[Tuple[str, str]], Dict[str, Any], None]


class AsyncClient:
    def __init__(self, get_session: Optional[SessionFactory] = None) -> None:
        self._get_session = get_session

    @property
    def session(self):
        if factory := self._get_session:
            return factory()

        return aiohttp.ClientSession()

    async def _request_json(self, session: aiohttp.ClientSession, args: UrlParams):
        response = await session.get(
            args.url,
            params=args.params,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        json = await response.json()
        return json
