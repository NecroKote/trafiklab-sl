from typing import Any, Dict, List, NamedTuple, Tuple, Union

import aiohttp


class UrlParams(NamedTuple):
    url: str
    params: Union[List[Tuple[str, str]], Dict[str, Any], None]


class AsyncClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _request_json(self, args: UrlParams):
        response = await self._session.get(
            args.url,
            params=args.params,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        json = await response.json()
        return json
