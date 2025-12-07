from tsl.helpers.cache import CacheProtocol


class MockCache(CacheProtocol):
    """Mock cache implementation for testing."""

    def __init__(self):
        self._data = {}

    async def get(self, key: str):
        return self._data.get(key)

    async def set(self, key: str, value, ttl: int | None = None):
        self._data[key] = value

    async def delete(self, key: str):
        self._data.pop(key, None)
