#
import os
from qmlutil.aux.xml import validate

PWD = os.path.dirname(__file__)

qmlfile = os.path.join(PWD, "data", "quakeml.xml")


def test_validate():
    """Test QuakeML validator fxn with known good QuakeML file"""
    with open(qmlfile) as f:
        assert validate(f)


