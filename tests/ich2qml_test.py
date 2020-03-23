#
"""
Test Ichinose solution converter
"""
import os
from qmlutil.ichinose import IchinoseToQmlConverter

PWD = os.path.dirname(__file__)
MT_FILE_v2 = os.path.join(PWD, 'data', 'mt_509589_v2.1-dev.txt')
MT_FILE_v3 = os.path.join(PWD, 'data', 'mt_719663_v3.0.6.txt')

# TODO: this is a patch b/c version was updated w/ no testing/notification
# Need to add all specific tests from file here: see v2 tests
# For now, just make sure the conversion happened w/o errors
#
def test_ichi_v3():
    with open(MT_FILE_v3) as f:
        conv = IchinoseToQmlConverter(f)
        event = conv.get_event()

    fm = event.get('focalMechanism')[0]
    origin = event.get('origin')[0]
    mag = event.get('magnitude')[0]
    
    assert mag.get('mag').get('value') == 4.53


def test_ichi_v2():
    with open(MT_FILE_v2) as f:
        conv = IchinoseToQmlConverter(f)
        event = conv.get_event()

    fm = event.get('focalMechanism')[0]
    origin = event.get('origin')[0]
    mag = event.get('magnitude')[0]
    
    # FocalMech
    assert fm.get('@publicID') == "smi:local/ichinose/509589-1238625-1441680946#focalmech"
    assert fm.get('triggeringOriginID') == "smi:local/origin/1238625"
    
    mt = fm.get('momentTensor', {})
    assert mt.get('@publicID') == "smi:local/ichinose/509589-1238625-1441680946#mt"
    assert mt.get('derivedOriginID') == "smi:local/ichinose/509589-1238625-1441680946#origin"
    assert mt.get('momentMagnitudeID') == "smi:local/ichinose/509589-1238625-1441680946#mag"
    # TODO: verify scalarMoment, dataUsed, doubleCouple, clvd, variance,
    # varianceReduction, tensor

    # Origin
    assert origin.get('@publicID') == "smi:local/ichinose/509589-1238625-1441680946#origin"
    assert origin.get('latitude', {}).get('value') == 38.6488
    assert origin.get('longitude', {}).get('value') == -118.8064
    assert origin.get('depth', {}).get('value') == 8000
    assert origin.get('time', {}).get('value') == "2015-09-08T02:15:21.000000Z"
    
    # Magnitude
    assert mag.get('@publicID') == "smi:local/ichinose/509589-1238625-1441680946#mag"
    assert mag.get('mag').get('value') == 3.95

