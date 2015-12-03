# -*- coding: utf-8 -*-
"""
qmlutil.css.css2qml

    Mark C. Williams (2015)
    Nevada Seismological Laboratory

    Converter classes to map CSS3.0 to QuakeML schema


Classes
=======
CSSToQMLConverter : methods to convert CSS to QuakeML schema
---------------------
USE: 
>>> c = CSSToQuakeMLConverter(
...    agency='NN',
...    rid_factory=ResourceURIGenerator('quakeml', 'org.nvseismolab'),
...    utc_factory=timestamp2isostr
...    )


NOTES
-----
This is a shot at implementing a schema converter in pure python. The goal is 
to enable dict->dict conversion between formats. There are some caveats, based
on the schemas:

1) CSS3.0 input dicts can contain joined, or "view" records for completeness.
2) CSS3.0 view keys are namespaced by table for uniqueness (only if necessary)
3) This QML schema uses 'xmltodict' style (for keys, dicts, lists). This means
   it's maybe incompatible with JSON-LD. Hopefully falls under YAGNI.

"""
import math
import datetime
import uuid

try:
    from collections import OrderedDict as Dict
except ImportError as e:
    Dict = dict

# Namespaces used by the XML serializer
Q_NAMESPACE ="http://quakeml.org/xmlns/quakeml/1.2"       # xmlns:q
CATALOG_NAMESPACE = "http://anss.org/xmlns/catalog/0.1"   # xmlns:catalog
BED_NAMESPACE = "http://quakeml.org/xmlns/bed/1.2"        # xmlns
BEDRT_NAMESPACE = "http://quakeml.org/xmlns/bed-rt/1.2"   # xmlns
CSS_NAMESPACE = 'http://www.seismo.unr.edu/schema/css3.0' # xmlns:css

# Time format for string
RFC3339 = '%Y-%m-%dT%H:%M:%S.%fZ'

# Default weight to use based on timedef
TIMEDEF_WEIGHT = dict(d=1.0, n=0.0)

# Default CSS3.0 etypes to QML event types
ETYPE_MAP = {
    'qb' : "quarry blast",
    'eq' : "earthquake",
    'me' : "meteorite",
    'ex' : "explosion",
    'o'  : "other event",
    'l'  : "earthquake",
    'r'  : "earthquake",
    't'  : "earthquake",
    'f'  : "earthquake",
}


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
    """Returns the UTC datetime in RFC3339-ISO8601"""
    try:
        return rfc3339(_dt(timestamp))
    except:
      return None


def _str(item):
    """Return a string no matter what"""
    if item is not None:
        return str(item)
    else:
        return ''


def _km2m(dist):
    """Convert from km to m only if dist is not None"""
    if dist is not None:
        return dist * 1000.
    else:
        return None


def _m2deg_lat(dist):
    return dist / 110600.


def _m2deg_lon(dist, lat=0.):
    M = 6367449.
    return dist / (math.pi / 180.) / M / math.cos(math.radians(lat))


def _eval_ellipse(a, b, angle):
    return a*b/(math.sqrt((b*math.cos(math.radians(angle)))**2 +
                          (a*math.sin(math.radians(angle)))**2))


def _get_NE_on_ellipse(A, B, strike):
    """
    Return the solution for points N and E on an ellipse
    
    A : float of semi major axis
    B : float of semi minor axis
    strike : angle of major axis from North

    Returns
    -------
    n, e : floats of ellipse solution at north and east
    """
    n = _eval_ellipse(A, B, strike)
    e = _eval_ellipse(A, B, strike-90)
    return n, e


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


class CSSToQMLConverter(object):
    """
    Converter to QuakeML schema from CSS3.0 schema

    Attributes
    ----------
    agency  : str of short agency identifier (net code)
    automatic_authors : list of authors to mark as "auto"
    rid_factory : ResourceUIDGenerator function which returns ID's
    utc_factory : function that converts a float timestamp

    Methods
    -------
    get_event_type : static class method to convert CSS origin type flag

    """
    #nsmap = {'css': CSS_NAMESPACE} # NS to use for extra css elements/attrib
    
    _auth_id = "local"  # default to use if rid_factory is N/A
    
    etype_map = dict(ETYPE_MAP)
    rid_factory = None
    utc_factory = None # function(timestamp: float) 
    agency  = 'XX'    # agency ID, ususally net code
    automatic_authors = []  # list of authors to mark as automatic
    
    @property
    def auth_id(self):
        """authority-id"""
        try:
            return self.rid_factory.authority_id or self._auth_id
        except:
            return self._auth_id

    def get_event_type(self, etype):
        """
        Map a CSS3.0 etype origin flag to a QuakeML event type
        
        Inputs
        ------
        etype : str of a valid etype
        """
        return self.etype_map.get(etype, "not reported")
 
    def origin_event_type(self, origin, emap=None):
        """Return a proper event_type from a CSS3.0 etype flag stored in an origin"""
        # TODO: fix namespace/strategy?
        if 'css:etype' in origin:
            etype = origin['css:etype']
            return self.get_event_type(etype)
        else:
            return "not reported"
    
    def get_event_status(self, posted_author):
        """
        Return mode and status based on author
        """
        for auto_author in self.automatic_authors:
            if not posted_author or auto_author in posted_author:
                mode = "automatic"
                status = "preliminary"
                return mode, status
        mode = "manual"
        status = "reviewed"
        return mode, status

    def __init__(self, *args, **kwargs):
        """
        Set event
        """
        self.event = Dict()
        
        # Allow setting of map at class level by noclobber update
        if 'etype_map' in kwargs:
            etype_map = kwargs.pop('etype_map')
            _etypemap = dict(self.etype_map)
            _etypemap.update(etype_map)
            self.etype_map = _etypemap
        
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
        
        if self.rid_factory is None:
            self.rid_factory = ResourceURIGenerator()
    
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

    def map_origin2origin(self, db):
        """
        Return a dict of QuakeML origin from a dict of CSS key/values
        
        Inputs
        ======
        db : dict of key/values of CSS fields related to the origin (see Join)

        Returns
        =======
        dict of key/values of QuakeML fields of "origin"

        Notes
        =====
        Any object that supports the dict 'get' method can be passed as
        input, e.g. OrderedDict, custom classes, etc.
        
        Join
        ----
        origin <- origerr [orid] (outer)
        """
        posted_author = _str(db.get('auth'))
        mode, status = self.get_event_status(posted_author)
        originID_rid = "{0}/{1}".format('origin', db.get('orid') or uuid.uuid4())
        
        #-- Basic Hypocenter ----------------------------------------
        origin = Dict([
            ('@publicID', self._uri(originID_rid)),
            ('latitude', Dict(value = db.get('lat'))),
            ('longitude', Dict(value = db.get('lon'))),
            ('depth', Dict(value = _km2m(db.get('depth')))),
            ('time', Dict(value = self._utc(db.get('time')))),
            ('quality' , Dict([
                ('standardError', db.get('sdobs')),
                ('usedPhaseCount', db.get('ndef')),
                ('associatedPhaseCount', db.get('nass')),
                ]),
            ),
            ('evaluationMode', mode),
            ('evaluationStatus', status),
            ('creationInfo', Dict([
                ('creationTime', self._utc(db.get('lddate'))),
                ('agencyID', self.agency), 
                ('author', posted_author),
                ('version', db.get('orid')),
                ])
            ),
        ])
        
        #-- Solution Uncertainties ----------------------------------
        # in CSS the ellipse is projected onto the horizontal plane
        # using the covariance matrix
        a = _km2m(db.get('smajax'))
        b = _km2m(db.get('sminax'))
        s = db.get('strike')
        dep_u = _km2m(db.get('sdepth'))
        time_u = db.get('stime')
        
        # There can be multiple uncertainties -- only add if exists 
        uncertainty = Dict([
            ('preferredDescription', "horizontal uncertainty"),
            ('horizontalUncertainty', a),
            ('maxHorizontalUncertainty', a),
            ('minHorizontalUncertainty', b),
            ('azimuthMaxHorizontalUncertainty', s),
        ])
        if db.get('conf') is not None:
            uncertainty['confidenceLevel'] = db.get('conf') * 100.  

        if uncertainty['horizontalUncertainty'] is not None:
            origin['originUncertainty'] = uncertainty

        #-- Parameter Uncertainties ---------------------------------
        if all([a, b, s]):
            n, e = _get_NE_on_ellipse(a, b, s)
            lat_u = _m2deg_lat(n)
            lon_u = _m2deg_lon(e, lat=origin['latitude']['value'])
            origin['latitude']['uncertainty'] = lat_u
            origin['longitude']['uncertainty'] = lon_u
        if dep_u:
            origin['depth']['uncertainty'] = dep_u
        if time_u:
            origin['time']['uncertainty'] = time_u

        # Save etype per origin due to schema differences...
        # TODO: add namespace to top node OR use explicitly
        css_etype = _str(db.get('etype'))
        #origin[self.nsmap['css']+':etype'] = css_etype
        origin['css:etype'] = css_etype

        return origin
    
    def map_stamag2stationmagnitude(self, db):
        """
        Map stamag record to StationMagnitude
        """
        originID_rid = "{0}/{1}".format('origin', db.get('orid') or uuid.uuid4())
        stamagID_rid = "{0}/{1}-{2}-{3}-{4}".format(
            'stamag',
            db.get('sta'),
            db.get('magtype'),
            db.get('orid') or uuid.uuid4(),
            db.get('magid') or uuid.uuid4(),
        )
        
        stationmagnitude = Dict([
            ('@publicID', self._uri(stamagID_rid)),
            ('mag', Dict([
                ('value', db.get('magnitude')),
                ('uncertainty', db.get('uncertainty')),
                ]),
            ),
            ('type', db.get('magtype')),
            ('creationInfo', Dict([
                ('creationTime', self._utc(db.get('lddate'))),
                ('agencyID', self.agency),
                ('author', db.get('auth')),
                ('version', db.get('magid')),
                ]),
            ),
            ('originID', self._uri(originID_rid)),
        ])
        return stationmagnitude

    def map_netmag2magnitude(self, db):
        """
        Return a dict of QuakeML magnitude from a dict of CSS key/values
        corresponding to one record.
        
        Inputs
        ======
        db : dict of key/values of CSS fields from the 'netmag' table

        Returns
        =======
        dict of key/values of QuakeML fields of "magnitude"

        Notes
        =====
        Any object that supports the dict 'get' method can be passed as
        input, e.g. OrderedDict, custom classes, etc.
        """
        posted_author = _str(db.get('auth'))
        mode, status = self.get_event_status(posted_author)
        originID_rid = "{0}/{1}".format('origin', db.get('orid') or uuid.uuid4())
        netmagID_rid = "{0}/{1}".format('netmag', db.get('magid') or uuid.uuid4())
        
        magnitude = Dict([
            ('@publicID', self._uri(netmagID_rid)),
            ('mag', Dict([
                ('value', db.get('magnitude')),
                ('uncertainty', db.get('uncertainty')),
                ])
            ),
            ('type', db.get('magtype')),
            ('stationCount', db.get('nsta')),
            ('originID', self._uri(originID_rid)),
            ('evaluationMode', mode),
            ('evaluationStatus', status),
            ('creationInfo', Dict([
                ('creationTime', self._utc(db.get('lddate'))),
                ('agencyID', self.agency),
                ('author', posted_author),
                ('version', db.get('magid')),
                ])
            ),
        ])
        return magnitude

    def map_origin2magnitude(self, db, mtype='ml'):
        """
        Return a dict of magnitude from an dict of CSS key/values
        corresponding to one record.
        
        Inputs
        ======
        db : dict of key/values of CSS fields from the 'origin' table
        mtype : str of valid field from origin to use as mag ('ml', 'mb') etc

        Returns
        =======
        dict of key/values of QuakeML fields of "magnitude"

        Notes
        =====
        Any object that supports the dict 'get' method can be passed as
        input, e.g. OrderedDict, custom classes, etc.
        """
        author = db.get('auth')
        originID_rid = "{0}/{1}".format('origin', db.get('orid') or uuid.uuid4())
        origmagID_rid = "{0}/{1}".format('origin-{0}'.format(mtype), db.get('orid') or uuid.uuid4())
        
        if author.startswith('orb'):
            status = "preliminary"
        else:
            status = "reviewed"
        
        magnitude = Dict([
            ('@publicID', self._uri(originID_rid)),
            ('mag', Dict(value = db.get(mtype))),
            ('type', mtype),
            ('originID', self._uri(originID_rid)),
            ('evaluationStatus', status),
            ('creationInfo', Dict([
                ('creationTime', self._utc(db.get('lddate'))), 
                ('agencyID', self.agency),
                ('version', db.get('orid')),
                ('author', author),
                ])
            ),
        ])
        return magnitude
    
    def map_arrival2pick(self, db):
        """
        Experimental map of just CSS arrival to QML pick.
        
        IF snetsta and schanloc are joined, will use those for SEED SNCL.
        Otherwise, will just use your converter agencyID for net and the 
        sta/chan recorded with the pick.

        Inputs
        ======
        db : dict of key/values of CSS fields related to the phases (see Join)

        Returns
        =======
        dict of QuakeML schema for Pick type

        Notes
        =====
        Any object that supports the dict 'get' method can be passed as
        input, e.g. OrderedDict, custom classes, etc.
        
        Join
        ----
        arrival <- snetsta [sta] (outer) <- schanloc [sta chan] (outer)
        """
        def_net = self.agency[:2].upper()
        css_sta = db.get('sta')
        css_chan = db.get('chan')
        wfID_rid = "{0}/{1}-{2}-{3}".format(
            'wfdisc', 
            css_sta,
            css_chan,
            int(db.get('time') * 10**6),
        )
        pickID_rid = "{0}/{1}".format('arrival', db.get('arid') or uuid.uuid4())
        
        
        on_qual = _str(db.get('qual')).lower()
        if 'i' in on_qual:
            onset = "impulsive"
        elif 'e' in on_qual:
            onset = "emergent"
        elif 'w' in on_qual:
            onset = "questionable"
        else:
            onset =  None
        
        pol = _str(db.get('fm')).lower()
        if 'c' in pol or 'u' in pol:
            polarity = "positive"
        elif 'd' in pol or 'r' in pol:
            polarity = "negative"
        elif '.' in pol:
            polarity = "undecidable"
        else:
            polarity = None
        
        pick_mode = "automatic"
        if 'orbassoc' not in _str(db.get('auth')):
            pick_mode = "manual"
        
        pick_status = "preliminary"
        if pick_mode is "manual":
            pick_status = "reviewed"
        
        pick = Dict([
            ('@publicID', self._uri(pickID_rid)),
            ('time', Dict([
                ('value', self._utc(db.get('time'))),
                ('uncertainty', db.get('deltim')),
                ])
            ),
            ('waveformID', Dict([
                ('@stationCode', db.get('fsta') or css_sta), 
                ('@channelCode', db.get('fchan') or css_chan),
                ('@networkCode', db.get('snet') or def_net),
                ('@locationCode', db.get('loc') or ""),
                ('resourceURI', self._uri(wfID_rid)),
                ])
            ),
            ('phaseHint', Dict(code=db.get('iphase'))),
            ('polarity', polarity),
            ('onset', onset),
            ('creationInfo', Dict([
                ('creationTime', self._utc(db.get('arrival.lddate') or db.get('lddate'))), 
                ('agencyID', self.agency), 
                ('author', db.get('auth')),
                ('version', db.get('arid')), 
                ])
            ),
            ('evaluationMode', pick_mode),
            ('evaluationStatus', pick_status),
            #('backazimuth', Dict([('value, db.get('azimuth')), ('uncertainty', db.get('delaz'))])),
            #('horizontalSlowness', Dict([('value', db.get('slow')), ('uncertainty', db.get('delslo'))])),
        ])
        return pick
    
    def map_assoc2arrival(self, db):
        """
        Experimental to map CSS assoc just to QML arrival

        Inputs
        ======
        db : dict of key/values of CSS fields related to the phases (see Join)

        Returns
        =======
        dict of QuakeML Arrival type

        Notes
        =====
        Any object that supports the dict 'get' method can be passed as
        input, e.g. OrderedDict, custom classes, etc.
        
        Join
        ----
        assoc
        """
        css_timedef = _str(db.get('timedef'))
        pickID_rid = "{0}/{1}".format('arrival', db.get('arid') or uuid.uuid4())
        vmodelID_rid = "{0}/{1}".format('vmodel', db.get('vmodel') or uuid.uuid4())
        assocID_rid = "{0}/{1}-{2}".format(
            'assoc',
            db.get('orid') or uuid.uuid4(), 
            db.get('arid') or uuid.uuid4(),
        )
        
        arr = Dict([
            ('@publicID', self._uri(assocID_rid)),
            ('pickID', self._uri(pickID_rid)),
            ('phase', db.get('phase')),
            ('azimuth', db.get('esaz')),
            ('distance', db.get('delta')),
            ('timeResidual', db.get('timeres')),
            ('timeWeight', db.get('wgt')),
            ('earthModelID', self._uri(vmodelID_rid, authority_id="local", schema="smi")),
            ('creationInfo', Dict([
                ('creationTime', self._utc(db.get('lddate'))),
                ('agencyID', self.agency),
                ('version', db.get('arid')),
                ])
            ),
            ('css:timedef', css_timedef),
        ])

        # Assign a default weight based on timedef if none in db
        if arr.get('timeWeight') is None:
            arr['timeWeight'] = TIMEDEF_WEIGHT.get(css_timedef)
        
        return arr

    def map_assocarrival2pickarrival(self, db):
        """
        Return tuple of quakeML (pick, arrival) from a dict of CSS key/values
        corresponding to one record. See the 'Join' section for the implied
        database table join expected.
        
        Inputs
        ======
        db : dict of key/values of CSS fields related to the phases (see Join)

        Returns
        =======
        tuple of dicts of key/values of QuakeML: ("pick", "arrival")

        Notes
        =====
        Any object that supports the dict 'get' method can be passed as
        input, e.g. OrderedDict, custom classes, etc.
        
        Join
        ----
        assoc <- arrival [arid] <- snetsta [sta] (outer) <- schanloc [sta chan] (outer)
        """
        pick = self.map_arrival2pick(db)
        arrival = self.map_assoc2arrival(db)
        return (pick, arrival)

    def map_fplane2focalmech(self, db):
        """
        Return a dict of focalMechanism from an dict of CSS key/values
        corresponding to one record. See the 'Join' section for the implied
        database join expected.
        
        Inputs
        ======
        db : dict of key/values of CSS fields from the 'fplane' table

        Returns
        =======
        dict of key/values of QuakeML "focalMechansim"

        Notes
        =====
        Any object that supports the dict 'get' method can be passed as
        input, e.g. OrderedDict, custom classes, etc.
        """
        #
        # NOTE: Antelope schema for this is wrong, no nulls defined
        # 
        originID_rid = "{0}/{1}".format('origin', db.get('orid') or uuid.uuid4())
        fplaneID_rid = "{0}/{1}".format('fplane', db.get('mechid') or uuid.uuid4())
        author_string = ':'.join([db.get('algorithm'), db.get('auth')])

        nodal_planes = Dict([
            ('nodalPlane1', Dict([
                ('strike', Dict(value = db.get('str1'))),
                ('dip', Dict(value = db.get('dip1'))),
                ('rake', Dict(value = db.get('rake1'))),
                ])
            ),
            ('nodalPlane2', Dict([
                ('strike', Dict(value = db.get('str2'))),
                ('dip', Dict(value = db.get('dip2'))),
                ('rake', Dict(value = db.get('rake2'))),
                ])
            ),
            ('@preferredPlane', 1),
        ])

        principal_axes = Dict([
            ('tAxis', Dict([
                ('azimuth', Dict(value = db.get('taxazm'))),
                ('plunge', Dict(value = db.get('taxplg'))),
                ])
            ),
            ('pAxis', Dict([
                ('azimuth', Dict(value = db.get('paxazm'))),
                ('plunge', Dict(value = db.get('paxplg'))),
                ])
            ),
        ])

        fm = Dict([
            ('@publicID', self._uri(fplaneID_rid)),
            ('triggeringOriginID', self._uri(originID_rid)),
            ('nodalPlanes', nodal_planes),
            ('principalAxes', principal_axes),
            ('creationInfo', Dict([
                ('creationTime', self._utc(db.get('lddate'))), 
                ('agencyID', self.agency),
                ('author', db.get('auth')),
                ('version', db.get('mtid')), 
                ])
            ),
        ])
        return fm
    
    # TODO: also do 'moment'???
    def map_moment2focalmech(self, db):
        """
        Map moment record to a FocalMechanism
        """
        raise NotImplementedError("No moment tensor support yet")
    
    def map_mt2focalmech(self, db):
        """
        Map BRTT CSS table 'mt' record to a FocalMechanism
        
        Notes
        =====
        1) This should not be first choice, mt table lacks many attributes of a 
        moment tensor solution, only use if nothing else is available.

        2) This treats derived parameters weirdly, there can be an orid, but
        also derived lat/lon etc, which should be in the origin table? So this
        method uses orid as the triggering origin and ignores the derived
        origin parameters. A more comprehensive one would build
        origin/magnitude and make the necessary ID's but leaves that for other
        methods, i.e. map_mt2origin, map_mt2magnitude. There should be an "Mw"
        in the netmag table, not here.
        """
        originID_rid = "{0}/{1}".format('origin', db.get('orid') or uuid.uuid4())
        mtID_rid = "{0}/{1}".format('mt', db.get('mtid') or uuid.uuid4())
        mtfmID_rid = "{0}/{1}".format('mt-focalmech', db.get('mtid') or uuid.uuid4())
        
        moment_tensor = Dict([
            ('@publicID', self._uri(mtID_rid)),
            ('scalarMoment', db.get('scm')),
            ('doubleCouple', db.get('pdc')),
            ('tensor', Dict([
                ('Mrr', Dict(value=db.get('tmrr'))),
                ('Mtt', Dict(value=db.get('tmtt'))),
                ('Mpp', Dict(value=db.get('tmpp'))),
                ('Mrt', Dict(value=db.get('tmrt'))),
                ('Mrp', Dict(value=db.get('tmrp'))),
                ('Mtp', Dict(value=db.get('tmtp'))),
                ])
            ),
            ('creationInfo', Dict([
                ('creationTime', self._utc(db['lddate'])), 
                ('agencyID', self.agency),
                ('author', db.get('auth')),
                ('version', db.get('mtid')), 
                ])
            ),
        ])
        
        nodal_planes = Dict([
            ('nodalPlane1', Dict([
                ('strike', Dict(value = db.get('str1'))),
                ('dip', Dict(value = db.get('dip1'))),
                ('rake', Dict(value = db.get('rake1'))),
                ])
            ),
            ('nodalPlane2', Dict([
                ('strike', Dict(value = db.get('str2'))),
                ('dip', Dict(value = db.get('dip2'))),
                ('rake', Dict(value = db.get('rake2'))),
                ])
            ),
            ('@preferredPlane', 1),
        ])

        principal_axes = Dict([
            ('tAxis', Dict([
                ('azimuth', Dict(value = db.get('taxazm'))),
                ('plunge', Dict(value = db.get('taxplg'))),
                ('length', Dict(value = db.get('taxlength'))),
                ])
            ),
            ('pAxis', Dict([
                ('azimuth', Dict(value = db.get('paxazm'))),
                ('plunge', Dict(value = db.get('paxplg'))),
                ('length', Dict(value = db.get('paxlength'))),
                ])
            ),
            ('nAxis', Dict([
                ('azimuth', Dict(value = db.get('naxazm'))),
                ('plunge', Dict(value = db.get('naxplg'))),
                ('length', Dict(value = db.get('naxlength'))),
                ])
            ),
        ])
        
        fm = Dict([
            ('@publicID', self._uri(mtfmID_rid)),
            ('triggeringOriginID', self._uri(originID_rid)),
            ('nodalPlanes', nodal_planes),
            ('principalAxes', principal_axes),
            ('momentTensor', moment_tensor),
            ('creationInfo', Dict([
                ('creationTime', self._utc(db.get('lddate'))), 
                ('agencyID', self.agency),
                ('author', db.get('auth')),
                ('version', db.get('mtid')), 
                ])
            ),
        ])
        return fm
    
    def convert_origins(self, records):
        """
        Origin converter

        Inputs
        ======
        records : iterable sequence of dict-like database records

        Returns
        =======
        list of dict
        """
        return [self.map_origin2origin(row) for row in records]

    def convert_phases(self, records):
        """
        Phase (Pick + Arrival) converter

        Inputs
        ======
        records : iterable sequence of dict-like database records

        Returns : tuple of (picks, arrivals) where
        =======
        picks    : list of dict
        arrivals :  list of dict
        """
        pick_arr_pairs = [self.map_assocarrival2pickarrival(row) for row in records]
        return map(list, zip(*pick_arr_pairs))

    def convert_focalmechs(self, records, schema='fplane'):
        """
        FocalMechanism converter

        Inputs
        ======
        records : iterable sequence of dict-like database records
        schema : str name of CSS table indicating input type

        Returns
        =======
        list of dict

        Notes
        =====
        FocalMechanisms can be from first-motion or moment tensor inversions,
        so the schema can be specified in the function call.
        """
        if schema == "fplane":
            return [self.map_fplane2focalmech(row) for row in records]
        elif schema == "mt":
            return [self.map_mt2focalmech(row) for row in records]
        else:
            pass  # schema == "moment" case too?
            
    @staticmethod
    def description(nearest_string, type="nearest cities"):
        """
        Return a dict eventDescription of type 'nearest cities'

        Inputs
        ======
        nearest_string : str of decription for the text field
        """
        return Dict(text=nearest_string, type=type)
    
    def map_event(self, db, anss=False):
        """
        Create a QML Event from a CSS event
        (will also accept a CSS origin row dict)
        """
        evid = db.get('evid')
        lddate = db.get('lddate')
        prefor = db.get('prefor') or db.get('orid')
        eventID_rid = "{0}/{1}".format('event', evid)
        
        event = Dict([
            ('@publicID', self._uri(eventID_rid)),
            ('type', "not reported"),
            ('creationInfo', Dict([
                ('creationTime', self._utc(lddate)),
                ('agencyID', self.agency),
                ('version', str(evid)),
                ])
            ),
        ])
        # Set the prefor if you gave on origin or the event table has one
        if prefor:
            originID_rid = "{0}/{1}".format('origin', prefor)
            event['preferredOriginID'] = self._uri(originID_rid)
        #
        # Add the ANSS NS parameters automatically
        #
        if anss:
            _agid = self.agency.lower()
            event['@catalog:eventid'] = "{0:08d}".format(evid)
            event['@catalog:dataid'] = "{0}{1:08d}".format(_agid, evid)
            event['@catalog:eventsource'] = _agid
            event['@catalog:datasource'] = _agid
        return event

    def event_parameters(self, **kwargs):
        """
        Create an EventParameters object

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
        qml = Dict([
            ('@xmlns:q', Q_NAMESPACE),
            ('@xmlns', default_namespace),
            ('@xmlns:css', CSS_NAMESPACE),
            ('@xmlns:catalog', CATALOG_NAMESPACE),
            ('eventParameters', event_parameters),
        ])
        return Dict({'q:quakeml': qml})

