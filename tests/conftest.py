from typing import List

import pytest

pytest_plugins = ("pytest_asyncio",)


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests",
    )


def pytest_configure(config: pytest.Config):
    config.addinivalue_line("markers", "integration: mark test as integration")


def pytest_collection_modifyitems(config: pytest.Config, items: List[pytest.Item]):
    if config.getoption("--integration"):
        return

    skip_integration = pytest.mark.skip(reason="need --integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
