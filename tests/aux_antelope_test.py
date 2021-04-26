#
import os

import pytest

PWD = os.path.dirname(__file__)

@pytest.mark.integration
def test_nearest_place():
    from qmlutil.aux.antelope import get_nearest_place
    
    dsn = PWD + "/data/db/dbplaces/nevada"
    coords = (-120.0321, 39.1284)
    p = get_nearest_place(dsn, coords)
    assert p == "9.1 km WNW of Glenbrook, NV"

