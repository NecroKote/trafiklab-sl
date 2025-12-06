import pytest

from tsl.utils import global_id_to_site_id


@pytest.mark.parametrize(
    "global_id, expected_site_id",
    [
        ("9091001000005730", 5730),
        ("9091001000009731", 9731),
    ],
)
def test_global_id_to_site_id(global_id, expected_site_id):
    assert global_id_to_site_id(global_id) == expected_site_id
