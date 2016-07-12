#
"""
Test qmlutil core functions
"""
import datetime

import qmlutil as qml


def test_resourceurigenerator():
    make_rid = qml.ResourceURIGenerator()

    rid = make_rid('foo')
    assert rid == "smi:local/foo"
    
    rid1 = make_rid("foo", "bar", schema="quakeml", authority_id="org.spam")
    assert rid1 == "quakeml:org.spam/foo#bar"

    make_rid2 = qml.ResourceURIGenerator(schema="quakeml", authority_id="org.spam")
    
    rid2 = make_rid2("foo", "bar")
    assert rid1 == rid2


def test_rfc3339():
    dt = datetime.datetime(2015, 01, 02, 15, 04, 56, 789000)
    assert qml.rfc3339(dt) == "2015-01-02T15:04:56.789000Z"


def test_ts2iso():
    assert qml.timestamp2isostr(1451397826.19485) == "2015-12-29T14:03:46.194850Z"
    assert qml.timestamp2isostr(None) is None


def test_find_preferred_mag():
    """Get mag id given list of types"""
    mags = [
        {
            "@publicID": "smi:local.test/netmag/123",
            "type": "md",
        },
        {
            "@publicID": "smi:local.test/netmag/121",
            "type": "mw",
        },
        {
            "@publicID": "smi:local.test/netmag/124",
            "type": "mw",
        },
        {
            "@publicID": "smi:local.test/netmag/122",
            "type": "ml",
        },
    ]
    pid = qml.find_preferred_mag(mags, ['mw', 'ml'])
    assert pid == "smi:local.test/netmag/124"
    pid = qml.find_preferred_mag(mags, ['mr', 'ml', 'md'])
    assert pid == "smi:local.test/netmag/122"


def test_get_preferred():
    """Test accessing item via publicID"""
    items = [
        {
            "@publicID": "smi:local.test/123",
        },
        {
            "@publicID": "smi:local.test/124",
        },
        {
            "@publicID": "smi:local.test/125",
        },
    ]
    i = qml.get_preferred("smi:local.test/125", items)
    assert i is items[2]


def test_anss_params():
    """Get a dict of ANSS stuff for QuakeML"""
    d = qml.anss_params("XX", 12345678)
    assert d['@catalog:eventid'] == "12345678"
    assert d['@catalog:dataid'] == "xx12345678"
    assert d['@catalog:datasource'] == "xx"
    assert d['@catalog:eventsource'] == "xx"
    

def test_extract_etype():
    """
    Test getting CSS etype from a comment tagged 'etype'
    """
    origin = {
        "comment": [
            {
                "@id": "smi:local.test/comment/867-5309",
                "text": "Jenny",
            },
            {
                "@id": "smi:local.test/origin/1234567#etype",
                "text": "LF",
            },
            {
                "@id": "smi:local.test/origin/1234567#comment",
                "text": "Fake event",
            },
        ],
    }
    etype = qml.extract_etype(origin)
    assert etype == "LF"


def test_station_count():
    """
    Test extracting unique station count from arrivals/picks
    """
    # make origin w/ arrival
    arrivals = [
        {
            "@publicID": "smi:local/assoc/00000000-10000001",
            "pickID": "smi:local/arrival/10000001",
            "timeWeight": 1.0,
        },
        {
            "@publicID": "smi:local/assoc/00000000-10000002",
            "pickID": "smi:local/arrival/10000002",
            "timeWeight": 0.0,
        },
        {
            "@publicID": "smi:local/assoc/00000000-10000003",
            "pickID": "smi:local/arrival/10000003",
            "timeWeight": 0.0,
        },
    ]
    picks = [
        {
            "@publicID": "smi:local/arrival/10000001",
            "waveformID": {"@networkCode":"XX", "@stationCode":"LAB1",
                "@channelCode": "HHZ",},
        },
        {
            "@publicID": "smi:local/arrival/10000002",
            "waveformID": {"@networkCode":"XX", "@stationCode":"LAB1",
                "@channelCode": "HHN",},
        },
        {
            "@publicID": "smi:local/arrival/10000003",
            "waveformID": {"@networkCode":"XX", "@stationCode":"LAB2",
                "@channelCode": "HHZ",},
        },
    ]
    assert qml.station_count(arrivals, picks) == 2
    assert qml.station_count(arrivals, picks, used=True) == 1
   
        
def test_qual_from_arrival():
    """
    Test calulating quality params from arrival data
    """
    arrivals = [
        {
            "@publicID": "smi:local/assoc/00000000-10000001",
            "pickID": "smi:local/arrival/10000001",
            "azimuth": 20.2,
            "distance": 1.2,
            "timeWeight": 1.0,
        },
        {
            "@publicID": "smi:local/assoc/00000000-10000002",
            "pickID": "smi:local/arrival/10000002",
            "azimuth": 20.2,
            "distance": 1.2,
            "timeWeight": 1.0,
        },
        {
            "@publicID": "smi:local/assoc/00000000-10000003",
            "pickID": "smi:local/arrival/10000003",
            "azimuth": 30.2,
            "distance": 2.3,
            "timeWeight": 0.0,
        },
        {
            "@publicID": "smi:local/assoc/00000000-10000004",
            "pickID": "smi:local/arrival/10000004",
            "azimuth": 90.3,
            "distance": 0.3,
            "timeWeight": 1.0,
        },
    ]
    qual = qml.get_quality_from_arrival(arrivals)
    assert qual['associatedStationCount'] == 3
    assert qual['usedStationCount'] == 2
    assert qual['minimumDistance'] == 0.3
    assert qual['maximumDistance'] == 2.3
    assert qual['azimuthalGap'] == 289.9


def test_root():
    """
    Test Root class
    """
    root = qml.Root()
    assert root.auth_id == "local"
    assert root._uri("foo", local_id="bar") == "smi:local/foo#bar"
    assert root._utc(1451397826.19485) == datetime.datetime(2015, 12, 29, 14, 3, 46, 194850)
    # TODO: init w/ utc_factory, check output
    ep = root.event_parameters(origin=[], focalMechanism=[], badelement=[])
    assert 'origin' in ep
    assert 'focalMechanism' in ep
    assert 'pick' not in ep
    assert 'badelement' not in ep
    assert ep.get('@publicID', '').startswith("smi:local/catalog/")

    cinfo = ep.get('creationInfo', {})
    assert cinfo.get('creationTime') is not None
    assert cinfo.get('version') is not None
    assert cinfo.get('agencyID') == "XX"

    qr = root.qml([], default_namespace="edu.unr.seismo")
    qm = qr.get('q:quakeml', {})
    assert 'eventParameters' in qm
    assert '@xmlns' in qm
    assert '@xmlns:q' in qm
    assert '@xmlns:catalog' in qm
    assert qm.get('@xmlns') == "edu.unr.seismo"

    #TODO: check event2root
    #

    

