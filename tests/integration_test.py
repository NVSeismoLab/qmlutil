#
"""
Integration tests
-----------------
Interact with other resources to get QuakeML data (i.e., Antelope DB)

These can be "slow" tests (several seconds), add flag to explicitly enable,
and wrap each whole function in decorator tag to prevent imports/running
unless you want to.

"""
import os
import pytest
#integration = pytest.mark.skipif(
#    not pytest.config.getoption("--integration"),
#    reason="Use --integration flag to run integration tests"
#)
integration = pytest.mark.integration

PWD = os.path.dirname(__file__)

#-- From flags/config
CFG = dict(
    agency_id = "NN",
    authority_id = "edu.unr.seismo",
    doi = "10.7914/SN/NN",
    etype_map = {
        'L': "earthquake",
        'LF': "earthquake",
        'f': "earthquake",
        'RN': "earthquake",
        'rn': "earthquake",
        'p': "explosion",
        'pL': "not reported",
        'im': "not reported",
        'ma': "not reported",
        'm': "not reported",
    },
    placesdb = PWD + '/data/db/dbplaces/nevada',
    preferred_magtypes = ['mw', 'ml', 'mb', 'md']
)

@pytest.mark.skip(reason="Issues opening DB")
@integration
def test_noprefor():
    """Test case of orid/evid in origin not in event table""" 
    import logging
    from qmlutil import dumps, Rounder
    from qmlutil.aux.xml import validate
    from qmlutil.aux.antelope import Db2Quakeml
    #from qmlutil.ichinose import IchinoseToQmlConverter

    # Preprocessor for XML serialization
    my_preproc = Rounder()

    #-- From args
    dsn = PWD + "/data/db/dbnoprefor/db"
    orid = 1414472
    evid = 540344

    # Convert and check for everything we asked for (ANSS, phases, etc)
    logging.basicConfig() # config root logger TODO: change to mudule logger:
    # 'qmlutil.aux.antelope'
    conv = Db2Quakeml(**CFG)
    # ------------------------------------------------------------------------
    # Test event generation
    event = conv.get_event(dsn, orid, pick=True, focalMechanism=True, anss=True)
    # Check event stuff, like anss...
    assert event['type'] == "earthquake" 
    if isinstance(event.get('description'), dict):
        assert event['description'].get('type') == "nearest cities"
    assert 'origin' in event and len(event['origin']) > 0
    assert 'magnitude' in event and len(event['magnitude']) > 0
    assert 'pick' in event and len(event['pick']) > 0
    assert event['@catalog:eventid'] == "00540344"
    assert event['@catalog:dataid'] == "nn00540344"
    assert event['@catalog:datasource'] == "nn"
    assert event['@catalog:eventsource'] == "nn"
    assert event['@publicID'] == "quakeml:edu.unr.seismo/event/540344"

    qmlroot = conv.event2root(event)
    assert isinstance(qmlroot, dict)
    assert 'q:quakeml' in qmlroot
    
    # Generate QuakeML and validate
    qmls = dumps(qmlroot, indent="  ", pretty=True, preprocessor=my_preproc)
    if pytest.config.getoption("--writefiles"):
        with open('/tmp/qmlutil-test-noprefor.xml', 'w') as f:
            f.write(qmls)
    assert validate(qmls)

@pytest.mark.skip(reason="Issues opening DB")
@integration
def test_nullphase():
    """Test case of no phase in arrival""" 
    import logging
    from qmlutil import dumps, Rounder
    from qmlutil.aux.xml import validate
    from qmlutil.aux.antelope import Db2Quakeml
    #from qmlutil.ichinose import IchinoseToQmlConverter

    # Preprocessor for XML serialization
    my_preproc = Rounder()

    #-- From args
    dsn = PWD + "/data/db/dbnullphase/db"
    orid = 1414472
    evid = 540344

    # Convert and check for everything we asked for (ANSS, phases, etc)
    logging.basicConfig() # config root logger TODO: change to mudule logger:
    # 'qmlutil.aux.antelope'
    conv = Db2Quakeml(**CFG)
    # ------------------------------------------------------------------------
    # Test event generation
    event = conv.get_event(dsn, orid, pick=True, focalMechanism=True, anss=True)
    # Check event stuff, like anss...
    assert event['type'] == "earthquake" 
    if isinstance(event.get('description'), dict):
        assert event['description'].get('type') == "nearest cities"
    assert 'origin' in event and len(event['origin']) > 0
    assert 'magnitude' in event and len(event['magnitude']) > 0
    assert 'pick' in event and len(event['pick']) > 0
    assert event['@catalog:eventid'] == "00540344"
    assert event['@catalog:dataid'] == "nn00540344"
    assert event['@catalog:datasource'] == "nn"
    assert event['@catalog:eventsource'] == "nn"
    assert event['@publicID'] == "quakeml:edu.unr.seismo/event/540344"

    qmlroot = conv.event2root(event)
    assert isinstance(qmlroot, dict)
    assert 'q:quakeml' in qmlroot
    
    # Generate QuakeML and validate
    qmls = dumps(qmlroot, indent="  ", pretty=True, preprocessor=my_preproc)
    if pytest.config.getoption("--writefiles"):
        with open('/tmp/qmlutil-test-nullphase.xml', 'w') as f:
            f.write(qmls)
    assert validate(qmls)

@integration
def test_magnitudes(request):
    """Test different magnitude scenarios""" 
    import logging
    from qmlutil import dumps, Rounder
    from qmlutil.aux.xml import validate
    from qmlutil.aux.antelope import Db2Quakeml
    from qmlutil.ichinose import IchinoseToQmlConverter

    # Preprocessor for XML serialization
    my_preproc = Rounder()

    #-- From args
    dsn = PWD + "/data/db/dbfull/reno"
    orid = 1371934
    evid = 524566

    # Convert and check for everything we asked for (ANSS, phases, etc)
    logging.basicConfig() # config root logger TODO: change to mudule logger:
    # 'qmlutil.aux.antelope'
    conv = Db2Quakeml(**CFG)
    
    # ------------------------------------------------------------------------
    # Test event generation
    event = conv.get_event(dsn, orid, pick=True, focalMechanism=True, #TODO:rm
            stationMagnitude=True, anss=True)
    # Check event stuff, like anss...
    assert event['type'] == "earthquake" 
    if isinstance(event.get('description'), dict):
        assert event['description'].get('type') == "nearest cities"
    assert 'origin' in event and len(event['origin']) > 0
    assert 'magnitude' in event and len(event['magnitude']) > 0
    assert 'pick' in event and len(event['pick']) > 0
    #assert 'focalMechanism' in event and len(event['focalMechanism']) > 0
    assert 'stationMagnitude' in event and len(event['stationMagnitude']) > 0
    assert event['@catalog:eventid'] == "00524566"
    assert event['@catalog:dataid'] == "nn00524566"
    assert event['@catalog:datasource'] == "nn"
    assert event['@catalog:eventsource'] == "nn"
    assert event['@publicID'] == "quakeml:edu.unr.seismo/event/524566"

    qmlroot = conv.event2root(event)
    assert isinstance(qmlroot, dict)
    assert 'q:quakeml' in qmlroot
    
    # Generate QuakeML and validate
    qmls = dumps(qmlroot, indent="  ", pretty=True, preprocessor=my_preproc)
    if request.config.getoption("--writefiles"):
        with open('/tmp/qmlutil-test-mag.xml', 'w') as f:
            f.write(qmls)
    assert validate(qmls)

@integration
def test_db2qml(request):
    """Test the whole integrated shebang""" 
    import logging
    from qmlutil import dumps, Rounder
    from qmlutil.aux.xml import validate
    from qmlutil.aux.antelope import Db2Quakeml
    from qmlutil.ichinose import IchinoseToQmlConverter

    # Preprocessor for XML serialization
    my_preproc = Rounder()

    #-- From args
    dsn = PWD + "/data/db/dbfull/reno"
    orid = 1371545
    evid = 524465

    # Convert and check for everything we asked for (ANSS, phases, etc)
    logging.basicConfig() # config root logger TODO: change to mudule logger:
    # 'qmlutil.aux.antelope'
    conv = Db2Quakeml(**CFG)
    
    # ------------------------------------------------------------------------
    # Test event generation
    event = conv.get_event(dsn, orid, pick=True, focalMechanism=True,
            stationMagnitude=True, anss=True)
    # Check event stuff, like anss...
    assert event['type'] == "earthquake"
    
    desc = event.get('description')
    if isinstance(desc, dict):
        assert desc.get('type') == "nearest cities"
    elif isinstance(desc, list):
        assert len(desc) == 2
        for d in desc:
            type_ = d.get("type", "")
            if type_ == "nearest cities":
                nc = d
            elif type_ == "earthquake name":
                en = d
        assert en.get("text") == "Example"

    assert 'origin' in event and len(event['origin']) > 0
    assert 'magnitude' in event and len(event['magnitude']) > 0
    assert 'pick' in event and len(event['pick']) > 0
    assert 'focalMechanism' in event and len(event['focalMechanism']) > 0
    assert 'stationMagnitude' in event and len(event['stationMagnitude']) > 0
    assert event['@catalog:eventid'] == "00524465"
    assert event['@catalog:dataid'] == "nn00524465"
    assert event['@catalog:datasource'] == "nn"
    assert event['@catalog:eventsource'] == "nn"
    assert event['@publicID'] == "quakeml:edu.unr.seismo/event/524465"

    qmlroot = conv.event2root(event)
    assert isinstance(qmlroot, dict)
    assert 'q:quakeml' in qmlroot
    
    # Generate QuakeML and validate
    qmls = dumps(qmlroot, indent="  ", pretty=True, preprocessor=my_preproc)
    if request.config.getoption("--writefiles"):
        with open('/tmp/qmlutil-test.xml', 'w') as f:
            f.write(qmls)
    assert validate(qmls)
    
    # ------------------------------------------------------------------------
    # Test delete from ORID
    event = conv.get_deleted_event(dsn, orid=orid, anss=True)
    assert event['type'] == "not existing" 
    assert event['@catalog:eventid'] == "00524465"
    assert event['@catalog:dataid'] == "nn00524465"
    assert event['@catalog:datasource'] == "nn"
    assert event['@catalog:eventsource'] == "nn"
    assert event['@publicID'] == "quakeml:edu.unr.seismo/event/524465"
    
    qmlroot = conv.event2root(event)
    assert isinstance(qmlroot, dict)
    assert 'q:quakeml' in qmlroot
    
    # Generate QuakeML and validate
    qmls = dumps(qmlroot, indent="  ", pretty=True, preprocessor=my_preproc)
    if request.config.getoption("--writefiles"):
        with open('/tmp/qmlutil-test-delete-orid.xml', 'w') as f:
            f.write(qmls)
    assert validate(qmls)
    
    # ------------------------------------------------------------------------
    # Test delete from EVID -- non-existing
    event = conv.get_deleted_event("/tmp/4c267822-3f72-4501-91fc-651851fd50a5", evid=evid, anss=True)
    assert event['type'] == "not existing" 
    assert event['@catalog:eventid'] == "00524465"
    assert event['@catalog:dataid'] == "nn00524465"
    assert event['@catalog:datasource'] == "nn"
    assert event['@catalog:eventsource'] == "nn"
    assert event['@publicID'] == "quakeml:edu.unr.seismo/event/524465"
    
    qmlroot = conv.event2root(event)
    assert isinstance(qmlroot, dict)
    assert 'q:quakeml' in qmlroot
    
    # Generate QuakeML and validate
    qmls = dumps(qmlroot, indent="  ", pretty=True, preprocessor=my_preproc)
    if request.config.getoption("--writefiles"):
        with open('/tmp/qmlutil-test-delete-evid.xml', 'w') as f:
            f.write(qmls)
    assert validate(qmls)
    
    # ------------------------------------------------------------------------
    # Test event with fplane focalmech
    orid = 1371240
    event = conv.get_event(dsn, orid, focalMechanism=True)
    # Check event stuff, like anss...
    assert event['type'] == "earthquake" 
    if isinstance(event.get('description'), dict):
        assert event['description'].get('type') == "nearest cities"
    assert 'origin' in event and len(event['origin']) > 0
    assert 'magnitude' in event and len(event['magnitude']) > 0
    assert 'focalMechanism' in event and len(event['focalMechanism']) > 0
    assert event['@publicID'] == "quakeml:edu.unr.seismo/event/524467"

    qmlroot = conv.event2root(event)
    assert isinstance(qmlroot, dict)
    assert 'q:quakeml' in qmlroot

    # Generate QuakeML and validate
    qmls = dumps(qmlroot, indent="  ", pretty=True, preprocessor=my_preproc)
    if request.config.getoption("--writefiles"):
        with open('/tmp/qmlutil-test-fm-524467.xml', 'w') as f:
            f.write(qmls)
    assert validate(qmls)
   
@integration
def test_ichinose_file(request):
    """Test building verified QuakeML from Ichinose solution file"""
    from qmlutil import (dumps, Rounder, ResourceURIGenerator, Root,
        timestamp2isostr)
    from qmlutil.aux.xml import validate
    from qmlutil.ichinose import IchinoseToQmlConverter
    
    # Preprocessor for XML serialization
    my_preproc = Rounder()
    
    # Test QuakeML file from text MT solution
    MT_FILE = os.path.join(PWD, 'data', "mt_719663_v3.0.6.txt") #'mt_509589_v2.1-dev.txt'
    with open(MT_FILE) as f:
        ichicnv = IchinoseToQmlConverter(
            f, 
            rid_factory=ResourceURIGenerator("quakeml", CFG['authority_id']), 
            utc_factory=timestamp2isostr,
            agency=CFG['agency_id'],
        )
        event = ichicnv.get_event(anss=True)
    
    # Check values from file here:
    assert 'origin' in event and len(event['origin']) > 0
   
    assert 'magnitude' in event and len(event['magnitude']) > 0
    mag = event['magnitude'][0]
    assert mag['mag'].get('value') == 4.53 # old v2 example: 3.95
    assert mag['type'] == "Mwr"

    assert 'focalMechanism' in event and len(event['focalMechanism']) > 0

    
    qmlroot = ichicnv.event2root(event)
    
    assert isinstance(qmlroot, dict)
    assert 'q:quakeml' in qmlroot
    # Generate QuakeML and validate
    qmls = dumps(qmlroot, indent="  ", pretty=True, preprocessor=my_preproc)
    if request.config.getoption("--writefiles"):
        with open('/tmp/qmlutil-test-ichinose-mt.v3.xml', 'w') as f:
            f.write(qmls)
    assert validate(qmls)
    

