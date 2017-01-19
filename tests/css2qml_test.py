#
"""
Test converting CSS values to QML
"""
import os
import json

from qmlutil import ResourceURIGenerator, timestamp2isostr
from qmlutil.css import CSSToQMLConverter as Converter, extract_etype


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


PWD = os.path.dirname(__file__)

with open(os.path.join(PWD, 'data', 'origin.json')) as f:
    CSS_ORIGIN = json.load(f)

with open(os.path.join(PWD, 'data', 'netmag1.json')) as f:
    CSS_NETMAG1 = json.load(f)

with open(os.path.join(PWD, 'data', 'netmag2.json')) as f:
    CSS_NETMAG2 = json.load(f)

with open(os.path.join(PWD, 'data', 'assocarrival.json')) as f:
    CSS_PICKS = json.load(f)

with open(os.path.join(PWD, 'data', 'mt.json')) as f:
    CSS_MT = json.load(f)

with open(os.path.join(PWD, 'data', 'fplane.json')) as f:
    CSS_FM = json.load(f)

with open(os.path.join(PWD, 'data', 'stamag.json')) as f:
    CSS_STAMAGS = json.load(f)

# make different from defaults
my_authority_id = "local.test"
my_agency_code = "QQ"
my_etype_map = {
    'L': "earthquake",
}

# TODO: Init converter, rid_factory in a setup/teardown
CONV = Converter(
    agency = my_agency_code,
    rid_factory = ResourceURIGenerator("quakeml", my_authority_id),
    utc_factory = timestamp2isostr,
    etype_map = my_etype_map,
    automatic_authors = ['orbassoc', 'orbmag'],
)


def test_map_origin():
    """
    Test converter for origins
    """
    csso = CSS_ORIGIN
    qmlo = CONV.map_origin2origin(csso)
    # Mandatory fields, covered by value tests???
    assert '@publicID' in qmlo
    assert 'latitude' in qmlo
    assert 'longitude' in qmlo
    assert 'depth' in qmlo
    assert 'time' in qmlo

    # Check values -- use isclose for floats
    assert qmlo.get('@publicID') == "quakeml:local.test/origin/1371545"
    assert isclose(qmlo.get('latitude', {}).get('value'), 41.8772)
    assert qmlo.get('latitude', {}).get('uncertainty') is not None
    assert isclose(qmlo.get('longitude', {}).get('value'), -119.6096)
    assert qmlo.get('longitude', {}).get('uncertainty') is not None
    assert isclose(qmlo.get('depth', {}).get('value'), 10020.5)
    assert isclose(qmlo.get('depth', {}).get('uncertainty'), 2220.8)
    assert qmlo.get('time', {}).get('value') == "2015-12-29T14:03:42.273110Z"
    assert isclose(qmlo.get('time', {}).get('uncertainty'), 0.31)
   
    assert extract_etype(qmlo) == "L"

    quality = qmlo.get('quality', {})
    assert isclose(quality.get('standardError'), 0.2141)
    assert quality.get('usedPhaseCount') == 14
    assert quality.get('associatedPhaseCount') == 37

    uncert = qmlo.get('originUncertainty', {})
    assert uncert.get('preferredDescription') == "uncertainty ellipse"
    assert isclose(uncert.get('maxHorizontalUncertainty'), 2902.0)
    assert isclose(uncert.get('minHorizontalUncertainty'), 2011.9)
    assert isclose(uncert.get('azimuthMaxHorizontalUncertainty'), 90.4)

    assert qmlo.get('evaluationMode') == "manual"
    assert qmlo.get('evaluationStatus') == "reviewed"

    cinfo = qmlo.get('creationInfo', {})
    assert cinfo.get('agencyID') == "QQ"
    assert cinfo.get('author') == "BRTT:tom"
    # May not be string
    #assert cinfo.get('version') == "1371545"
    # Check time format against regex? or within X min of test time?

    # Check auto_authors
    csso2 = dict(csso)
    csso2['auth'] = "orbassoc"
    qmlo = CONV.map_origin2origin(csso2)
    assert qmlo.get('evaluationMode') == "automatic"
    assert qmlo.get('evaluationStatus') == "preliminary"
    assert qmlo.get('creationInfo', {}).get('author') == "orbassoc"


def test_map_netmag():
    """
    Test converter for network magnitudes
    """
    cssm = CSS_NETMAG2
    qmlm = CONV.map_netmag2magnitude(cssm)
    
    assert '@publicID' in qmlm
    assert 'mag' in qmlm

    assert qmlm.get('@publicID') == "quakeml:local.test/netmag/296149"
    assert isclose(qmlm.get('mag', {}).get('value'), 3.45)
    assert isclose(qmlm.get('mag', {}).get('uncertainty'), 0.19)
    assert qmlm.get('type') == "ml"
    assert qmlm.get('stationCount') == 5
    
    assert qmlm.get('originID') == "quakeml:local.test/origin/1371545"
    assert qmlm.get('evaluationMode') == "manual"
    assert qmlm.get('evaluationStatus') == "reviewed"
    
    # TODO: additional fields, creationInfo, etc
    cinfo = qmlm.get('creationInfo', {})
    assert cinfo.get('agencyID') == "QQ"
    assert cinfo.get('author') == "dbml:tom"


def test_map_originmag():
    """
    Test converter for origin reported/saved magnitudes
    """
    csso = CSS_ORIGIN
    qmlm = CONV.map_origin2magnitude(csso)

    assert '@publicID' in qmlm
    assert 'mag' in qmlm

    assert qmlm.get('@publicID') == "quakeml:local.test/netmag/296149"
    assert isclose(qmlm.get('mag', {}).get('value'), 3.45)
    assert qmlm.get('type') == "ml"
    
    assert qmlm.get('originID') == "quakeml:local.test/origin/1371545"
    assert qmlm.get('evaluationMode') == "manual"
    assert qmlm.get('evaluationStatus') == "reviewed"
    
    cinfo = qmlm.get('creationInfo', {})
    assert cinfo.get('agencyID') == "QQ"
    assert cinfo.get('author') == "BRTT:tom"
    
    # Case of no netmag UID
    csso2 = dict(csso)
    csso2['mlid'] = None
    qmlm = CONV.map_origin2magnitude(csso2)
    assert qmlm.get('@publicID') == "quakeml:local.test/origin/1371545#ml"


def test_map_stamags():
    """
    Test converter for station magnitudes
    """
    cssm = CSS_STAMAGS[0]
    qmlm = CONV.map_stamag2stationmagnitude(cssm)

    assert '@publicID' in qmlm
    assert 'originID' in qmlm
    assert 'mag' in qmlm

    assert qmlm.get('@publicID') == "quakeml:local.test/stamag/LKVW-ml-1371545-296149"
    assert qmlm.get('originID') == "quakeml:local.test/origin/1371545"
    
    assert isclose(qmlm.get('mag', {}).get('value'), 3.13)
    assert qmlm.get('type') == "ml"
    
    cinfo = qmlm.get('creationInfo', {})
    assert cinfo.get('agencyID') == "QQ"
    assert cinfo.get('author') == "dbml:tom"

def test_map_stamag_contribs():
    """
    Test converter for station magnitude contributions
    """
    cssm = CSS_STAMAGS[0]
    qmlm = CONV.map_stamag2magnitudecontrib(cssm)

    assert qmlm.get('stationMagnitudeID') == "quakeml:local.test/stamag/LKVW-ml-1371545-296149"


def test_map_arrival():
    """Test converter for arrivals"""
    cssa = CSS_PICKS[0]
    qmlp = CONV.map_arrival2pick(cssa)

    assert '@publicID' in qmlp
    assert 'time' in qmlp
    assert 'waveformID' in qmlp

    assert 'value' in qmlp.get('time', {})
    wfid = qmlp.get('waveformID', {})
    assert '@stationCode' in wfid
    assert '@channelCode' in wfid

    assert qmlp.get('@publicID') == "quakeml:local.test/arrival/7001364"
    assert qmlp.get('time').get('value') == "2015-12-29T14:03:46.194850Z"
    assert isclose(qmlp.get('time').get('uncertainty'), 0.071)
    assert qmlp.get('waveformID', {}).get('#text', '').startswith("smi:local.test/wfdisc/COLR-HHZ")
    assert qmlp.get('waveformID', {}).get('@stationCode') == "COLR"
    assert qmlp.get('waveformID', {}).get('@channelCode') == "HHZ"
    assert qmlp.get('waveformID', {}).get('@networkCode') == "NN"

    assert qmlp.get('phaseHint') == "P"

    assert qmlp.get('evaluationMode') == "manual"
    assert qmlp.get('evaluationStatus') == "reviewed"


def test_map_assoc():
    """Test converter for associations"""
    cssa = CSS_PICKS[0]
    qmla = CONV.map_assoc2arrival(cssa)

    assert '@publicID' in qmla
    assert 'pickID' in qmla
    assert 'phase' in qmla

    assert qmla.get('@publicID') == "quakeml:local.test/assoc/1371545-7001364"
    assert qmla.get('pickID') == "quakeml:local.test/arrival/7001364"
    assert qmla.get('phase') == "P"


def test_map_mt():
    """Test converter for moment tensors in mt table"""
    cssm = CSS_MT
    qmlf = CONV.map_mt2focalmech(cssm)

    assert '@publicID' in qmlf
    assert 'momentTensor' in qmlf

    mt = qmlf.get('momentTensor', {})
    assert '@publicID' in mt
    assert 'derivedOriginID' in mt
    
    assert qmlf.get('@publicID') == "quakeml:local.test/mt/105#focalmech"
    assert mt.get('@publicID') == "quakeml:local.test/mt/105#tensor"

    # TODO: check other fields in focalmech, mt, tensor, creation, etc


def test_map_fplane():
    """Test converter for fplane focal mechanisms"""
    cssf = CSS_FM
    qmlf = CONV.map_fplane2focalmech(cssf)

    assert '@publicID' in qmlf
    
    assert qmlf.get('@publicID') == "quakeml:local.test/fplane/4257"
    assert qmlf.get('triggeringOriginID') == "quakeml:local.test/origin/1371240"
    
    nps = qmlf.get('nodalPlanes', {})
    pas = qmlf.get('principalAxes', {})
    
    np1 = nps.get('nodalPlane1')
    assert isclose(np1.get('strike', {}).get('value'), 320.5) 
    assert isclose(np1.get('dip', {}).get('value'), 56.6) 
    assert isclose(np1.get('rake', {}).get('value'), -118.5) 
    np2 = nps.get('nodalPlane2')
    assert isclose(np2.get('strike', {}).get('value'), 185.1) 
    assert isclose(np2.get('dip', {}).get('value'), 42.8) 
    assert isclose(np2.get('rake', {}).get('value'), -54.1) 

    t = pas.get('tAxis', {})
    assert isclose(t.get('azimuth', {}).get('value'), 70.4) 
    assert isclose(t.get('plunge', {}).get('value'), 7.4) 
    assert isclose(t.get('length', {}).get('value'), 0) 
    p = pas.get('pAxis', {})
    assert isclose(p.get('azimuth', {}).get('value'), 176.8) 
    assert isclose(p.get('plunge', {}).get('value'), 65.2) 
    assert isclose(p.get('length', {}).get('value'), 0) 

    cinfo = qmlf.get('creationInfo', {})
    assert cinfo.get('agencyID') == "QQ"
    assert cinfo.get('author') == "HASHpy:mcassar"
    
    assert qmlf.get('evaluationMode') == "manual"
    assert qmlf.get('evaluationStatus') == "reviewed"




