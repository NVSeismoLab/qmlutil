# -*- coding: utf-8 -*-
"""
Core/common for qmlutil packages

Mark C. Williams (2016)
Nevada Seismological Lab

"""
import datetime
import uuid
try:
    from collections import OrderedDict as Dict
except ImportError as e:
    Dict = dict

# Time format for string
RFC3339 = '%Y-%m-%dT%H:%M:%S.%fZ'

Q_NAMESPACE ="http://quakeml.org/xmlns/quakeml/1.2"       # xmlns:q
CATALOG_NAMESPACE = "http://anss.org/xmlns/catalog/0.1"   # xmlns:catalog
BED_NAMESPACE = "http://quakeml.org/xmlns/bed/1.2"        # xmlns
BEDRT_NAMESPACE = "http://quakeml.org/xmlns/bed-rt/1.2"   # xmlns


def _dt(timestamp):
    """Returns the UTC dateTime"""
    try:
        return datetime.datetime.utcfromtimestamp(timestamp)
    except:
      return None


def _ts(dt):
    """
    Return timestamp from datetime object
    """
    return (dt-datetime.datetime(1970, 01, 01, 00, 00, 00)).total_seconds()


def rfc3339(dt):
    """
    Format datetime in ISO8601
    """
    return dt.strftime(RFC3339)
    

def timestamp2isostr(timestamp):
    """
    Returns float epoch timestamp in RFC3339-ISO8601

    Note
    ----
    This is python wrapper middleware (fails silently)
    """
    try:
        return rfc3339(_dt(timestamp))
    except:
      return None


class ResourceURIGenerator(object):
    """
    Create function to generate URI's for QuakeML
    """
    _pattern = r"(smi|quakeml):[\w\d][\w\d\−\.\∗\(\)_~’]{2,}/[\w\d\−\.\∗\(\)_~’][\w\d\−\.\∗\(\)\+\?_~’=,;#/&amp;]∗" 
    schema = None
    authority_id = None

    def __init__(self, schema="smi", authority_id="local"):
        self.schema = schema
        self.authority_id = authority_id

    def __call__(self, resource_id=None, local_id=None, authority_id=None, schema=None):
        """
        Generate an id, given a resource-id and possible local-id, other parts
        can be overridden here as well
        """
        if not resource_id:
            resource_id = str(uuid.uuid4())
        schema = schema or self.schema
        auth_id = authority_id or self.authority_id
        rid = "{0}:{1}/{2}".format(schema, auth_id, resource_id)
        if local_id:
            rid += "#{0}".format(local_id)
        return rid

    def validate(rid):
        """Validate"""
        raise NotImplementedError("Not done yet")


def find_preferred_mag(mags, prefmaglist=[]):
    """
    Given a seq of mag dicts, return the id of the preferred one
    
    Note
    ----
    Returns the preferred of the last of any given type, so multiple 'mw'
    magnitudes will return the last one. If using reverse-sorted time
    magnitudes, (like the Database converter returns), need to pass in the
    reversed list, e.g. mags[::-1]
    """
    pid = None
    types = dict([(m.get('type', '').lower(), m['@publicID']) for m in mags])
    for pref in prefmaglist:
        pid = types.get(pref.lower())
        if pid is not None:
            return pid
    return pid


def anss_params(agency_id, evid):
    """
    Generate a dictionary of ANSS params for tagging events
    """
    _agid = agency_id.lower()
    d = dict([
        ('@catalog:eventid', "{0:08d}".format(evid)),
        ('@catalog:dataid', "{0}{1:08d}".format(_agid, evid)),
        ('@catalog:eventsource', _agid),
        ('@catalog:datasource', _agid),
    ])
    return d


def get_preferred(prefid, items):
    """
    Return item given a preferred publicID

    Notes: brute force, but works
    """
    for it in items:
        if it.get('@publicID') == prefid:
            return it


def station_count(arrivals, picks, used=False):
    """Return a station count"""
    if used:
        ids = [a['pickID'] for a in arrivals if 'pickID' in a and
            a.get('timeWeight', 0) > 0]
    else:
        ids = [a['pickID'] for a in arrivals if 'pickID' in a]
    stations = set()
    for i in ids:
        p = get_preferred(i, picks)
        w = p.get('waveformID')
        if w:
            stations.add("{0}_{1}".format(w['@networkCode'], w['@stationCode']))
    return len(stations)

    
class Root(object):
    """
    Generic QuakeML root

    Common methods for returning basic and high-level QuakeML elements as
    python dicts.

    Methods should return dicts of quakeml elements
    """
    _auth_id = "local"  # default to use if rid_factory is N/A
    
    agency  = 'XX'      # agency ID, ususally net code
    doi = None          # DOI without scheme
    rid_factory = None  # ResourceURIGenerator function
    utc_factory = None  # function(timestamp: float) 
    
    @property
    def auth_id(self):
        """authority-id"""
        try:
            return self.rid_factory.authority_id or self._auth_id
        except:
            return self._auth_id
    
    def _uri(self, obj=None, *args, **kwargs):
        """
        Return unique ResourceIdentifier URI
        """
        if obj is None:
            resource_id = str(uuid.uuid4())
        else:
            resource_id = str(obj)
        return self.rid_factory(resource_id, *args, **kwargs)
    
    def _utc(self, timestamp):
        """
        Return a time representation given seconds timestamp float

        (default is datetime.datetime object)
        """
        if self.utc_factory is None:
            return _dt(timestamp)
        else:
            return self.utc_factory(timestamp)
    
    def __init__(self, *args, **kwargs):
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
        
        if self.rid_factory is None:
            self.rid_factory = ResourceURIGenerator()
    
    def event_parameters(self, **kwargs):
        """
        Create an EventParameters object
        
        Return dict of eventParameters element given arrays of high-level
        elements as keywords i.e. event=[ev1, ev2, ev3].

        Should be valid for BED or BED-RT
        """
        allowed = ('event', 'origin', 'magnitude', 'stationMagnitude', 
            'focalMechanism', 'reading', 'pick', 'amplitude', 'description',
            'comment', 'creationInfo')
        
        dtnow = datetime.datetime.utcnow()
        ustamp = int(_ts(dtnow) * 10**6)
        catalogID_rid = "{0}/{1}".format('catalog', ustamp)
        
        eventParameters = Dict([
            ('@publicID', self._uri(catalogID_rid)),
            ('creationInfo', Dict([
                ('creationTime', self._utc(_ts(dtnow))),
                ('agencyID', self.agency),
                ('version', str(ustamp)),
                ])
            ),
        ])
        for k in kwargs:
            if k in allowed:
                eventParameters[k] = kwargs[k]
        return eventParameters
        
    # TODO: save nsmap in attributes, build as generator/mapped fxn
    def qml(self, event_parameters, default_namespace=BED_NAMESPACE):
        """
        Return dict of QuakeML root element given eventParameters dict
        """
        qml = Dict([
            ('@xmlns:q', Q_NAMESPACE),
            ('@xmlns', default_namespace),
            ('@xmlns:catalog', CATALOG_NAMESPACE),
            ('eventParameters', event_parameters),
        ])
        return Dict({'q:quakeml': qml})

    def event2root(self, ev):
        """
        Convenience method to add event to parameters and root
        Also appends evid to eventParameters publicID
        """
        event_id = ev.get('@publicID', '').split('/', 1)[-1].replace('/', '=')
        catalog = self.event_parameters(event=[ev])
        catalog['@publicID'] += "#{0}".format(event_id)
        if self.doi:
            catalog['creationInfo']['agencyURI'] = "smi:{0}".format(self.doi)
        qmlroot = self.qml(event_parameters=catalog)
        return qmlroot

