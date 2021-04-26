# -*- coding: utf-8 -*-
#
# Copyright 2016 University of Nevada, Reno
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
qmlutil.aux.antelope

Utillites for extracting data from Antelope -- 3rd party libs required
"""
from collections import OrderedDict as Dict, defaultdict
import datetime
import math
import logging

try:
    from antelope import datascope as antds
except ImportError:
    import os
    import site
    if not "ANTELOPE" in os.environ:
        raise ImportError("Can't import antelope, 'ANTELOPE' env var not set?")
    site.addsitedir(os.path.join(os.environ['ANTELOPE'],'data','python'))
    from antelope import datascope as antds

import qmlutil as qml
from qmlutil.css import extract_id


# This class replaces the lib for working with Antelope Datascope python
# ** tested with 5.6 ** -MCW
class Database(object):
    """
    Antelope Database utility method namespace
    """
    @classmethod
    def open(cls, dbname=None, **kwargs):
        """Open file or tmp file, diff kwargs are valid, returns ptr"""
        if dbname is None:
            return antds.dbtmp(**kwargs)
        return antds.dbopen(dbname, **kwargs)
    
    @classmethod
    def nullptr(cls, dbptr):
        nptr = antds.Dbptr(dbptr)
        nptr.record = antds.dbNULL
        return nptr
    
    @classmethod
    def schema(cls, dbptr):
        """
        Return description/attributes of the schema for a given pointer. Will
        create unique names for fields in a view with non-unique duplicates.
        """
        db = antds.Dbptr(dbptr)
        s = defaultdict(list)
        table_fields = db.query(antds.dbTABLE_FIELDS)
        s["primary_key"] = db.query(antds.dbPRIMARY_KEY)
        for db.field, name in enumerate(table_fields):
            # field names
            if name in table_fields[:db.field]:
                tablename = db.query(antds.dbFIELD_BASE_TABLE)
                name = '.'.join([tablename, name])
            s["fields"].append(name)
            # type codes
            type_code = db.query(antds.dbFIELD_TYPE)
            s["field_types"].append(type_code)
            # other features, may not be needed
            #s["field_sizes"].append(db.query(antds.dbFIELD_SIZE))
            #s["field_formats"].append(db.query(antds.dbFIELD_FORMAT))
        return s
    
    @classmethod
    def table_fields(cls, dbptr):
        """Return unique field names for a view, which Antelope does not do."""
        return cls.schema(dbptr).get("fields")
    
    @classmethod 
    def convert_times_in_row(cls, rawrow, type_codes):
        """
        Convert a row value into a datetime. ONLY supports float TIME for now.
        """
        vals = []
        for n, rawval in enumerate(rawrow):
            # NOTE: dbTIME is float, add dbYEARDAY int, make option?
            if type_codes[n] == antds.dbTIME and isinstance(rawval, float): 
                v = datetime.datetime.utcfromtimestamp(rawval)
            else:
                v = rawval
            vals.append(v)
        return vals

    @classmethod 
    def convert_null_row(cls, rawrow, nullrow):
        """
        Return a row where any null value for a field is a python None
        """
        if len(rawrow) != len(nullrow):
            raise ValueError("Rows are different lengths!")
        vals = []
        for n, nullval in enumerate(nullrow):
            if rawrow[n] == nullval:
                v = None
            else:
                v = rawrow[n]
            vals.append(v)
        return vals
    
    @classmethod
    def get_rows(cls, dbptr, convert_null=False, convert_time=False, as_dict=False):
        """
        Extract field names and row data from view pointer.

        Return fields and values suitable for use by the csv, json, or any
        DBAPI2 modules.

        This will pull every field from all rows the pointer is pointing to,
        can optionally:
            - convert NULL values to None 
            - convert times to datetime
            - return values as a dict instead of an ordered sequence of values.
        """
        dbptr = antds.Dbptr(dbptr)
        attr = cls.schema(dbptr)
        fields = attr.get("fields", [])
        types = attr.get("field_types", [])
        rows = []
        if convert_null:
            nullvals = cls.nullptr(dbptr).getv(*fields)
        for dbptr.record in range(dbptr.record_count):
            vals = dbptr.getv(*fields)
            if convert_null:
                vals = cls.convert_null_row(vals, nullvals)
            if convert_time:
                vals = cls.convert_times_in_row(vals, types)
            if as_dict:
                vals = Dict([(fields[n], v) for n, v in enumerate(vals)])
            rows.append(vals)
        return (fields, rows)


class DatabaseConverter(object):
    """
    Convert to QML given an Antelope database Connection

    Methods take an ORID, return QML elements/types
    """
    dbptr = None # antelope.datascope.Dbptr
    converter = None # converter class
    
    # Database get_rows options to use as defaults
    _rowopts = {}
    
    def rowopts(self, **kwargs):
        """
        Return copy of row options w/ substitutes
        """
        d = dict(self._rowopts)
        d.update(kwargs)
        return d

    def __init__(self, dbptr, converter):
        self.dbptr = dbptr
        self.converter = converter
        self._rowopts = {
            "convert_null": True,
            "as_dict": True,
        }
        
    def _evid(self, orid):
        """
        Get EVID from ORID
        """
        cmd = ['dbopen origin', 'dbsubset orid=={0}'.format(orid), 'dbsort lddate']
        db = self.dbptr.process(cmd)
        fields, rows = Database.get_rows(db, **self.rowopts())
        if rows:
            return rows[0].get('evid')

    def get_event(self, orid=None, evid=None, anss=False):
        if orid and not evid:
            evid = self._evid(orid)
        cmd = ['dbopen event', 'dbsubset evid=={0}'.format(evid)]
        db = self.dbptr.process(cmd)
        fields, rows = Database.get_rows(db, **self.rowopts())
        if rows:
            return self.converter.map_event(rows[0], anss=anss)
    
    def get_event_from_origin(self, orid=None, anss=False):
        """
        Get event from origin table (in case no event/prefor)
        """
        cmd = ['dbopen origin', 'dbsubset orid=={0}'.format(orid)]
        db = self.dbptr.process(cmd)
        fields, rows = Database.get_rows(db, **self.rowopts())
        if rows:
            return self.converter.map_event(rows[0], anss=anss)

    def get_focalmechs(self, orid=None):
        """
        Returns FocalMechanism instances of an ORID
        
        Inputs
        ------
        orid : int of ORID

        Returns
        -------
        list of FocalMechanism types

        """
        cmd = ['dbopen fplane', 'dbsubset orid=={0}'.format(orid), 
            'dbsort -r lddate']
        db = self.dbptr.process(cmd)
        rowopts = self.rowopts(convert_null=False) # Antelope schema bug - missing fplane NULLS
        fields, rows = Database.get_rows(db, **rowopts)
        return self.converter.convert_focalmechs(rows, "fplane")
    
    def get_mts(self, orid=None):
        """
        Returns FocalMechanism instances or ORID from mt table
        """
        cmd = ['dbopen mt', 'dbsubset orid=={0}'.format(orid), 
            'dbsort -r lddate']
        db = self.dbptr.process(cmd)
        fields, rows = Database.get_rows(db, **self.rowopts())
        return self.converter.convert_focalmechs(rows, "mt")

    def get_origins(self, orid=None, evid=None):
        """
        Returns Origin instances from an ORID or EVID
        
        Inputs
        ------
        orid : int of ORID 
        evid : int of EVID

        Returns
        -------
        list of Origin types

        """
        if orid is not None:
            substr = 'dbsubset orid=={0}'.format(orid)
        elif evid is not None:
            substr = 'dbsubset evid=={0}'.format(evid)
        else:
            raise ValueError("Need to specify an ORID or EVID")
        
        cmd = ['dbopen origin', 'dbjoin -o origerr', substr, 'dbsort -r lddate']
        db = self.dbptr.process(cmd)
        fields, rows = Database.get_rows(db, **self.rowopts())
        return self.converter.convert_origins(rows)
    
    def get_magnitudes(self, orid=None, evid=None):
        """
        Return list of Magnitudes from ORID
        
        Inputs
        ------
        orid : int of orid

        Returns
        -------
        list of Magnitude types
        
        Notes
        -----
        Right now, looks in 'netmag', then 'origin', and assumes anything in netmag
        is in 'origin', that may or may not be true...
        """
        mags = []
        # TODO: try evid first
        # evid = self._evid(orid)
        # substr = 'dbsubset evid=={0}'.format(evid)
        substr = 'dbsubset orid=={0}'.format(orid)
        
        # 1. Check netmag table
        cmd = ('dbopen netmag', substr, 'dbsort -r lddate')
        db = self.dbptr.process(cmd)
        fields, rows = Database.get_rows(db, **self.rowopts())
        if rows:
            mags += [self.converter.map_netmag2magnitude(r) for r in rows]
            return mags

        # 2. Check the origin table for the 3 types it holds
        cmd = ('dbopen origin', substr)
        db = self.dbptr.process(cmd)
        fields, rows = Database.get_rows(db, **self.rowopts())
        if rows:
            r = rows[0]
            mags += [self.converter.map_origin2magnitude(r, mtype=mtype) 
                     for mtype in ('ml', 'mb', 'ms') if r.get(mtype)]
        return mags
    
    def get_station_magnitudes(self, orid=None, evid=None, magid=None):
        """
        Return station magnitudes
        """
        if magid:
            query = 'magid=={0}'.format(magid)
        elif orid:
            query = 'orid=={0}'.format(orid)
        elif evid:
            query = 'evid=={0}'.format(evid)

        cmd = [
            'dbopen stamag', 
            'dbsubset {0}'.format(query),
            'dbjoin -o arrival', 'dbjoin -o snetsta',
            'dbjoin -o schanloc sta chan',
        ]
        db = self.dbptr.process(cmd)
        fields, rows = Database.get_rows(db, **self.rowopts())
        return self.converter.convert_magnitudes(rows)

    def get_phases(self, orid=None, evid=None):
        """
        Return lists of obspy Arrivals and Picks from an ORID
        
        Inputs
        ------
        int of ORID

        Returns : picks, arrivals
        -------
        picks    : list of Pick types
        arrivals :  list of Arrival types

        """
        cmd = ['dbopen assoc', 'dbsubset orid=={0}'.format(orid),
               'dbjoin arrival', 'dbjoin -o snetsta',
               'dbjoin -o schanloc sta chan']
        db = self.dbptr.process(cmd)
        fields, rows = Database.get_rows(db, **self.rowopts())
        return self.converter.convert_phases(rows)
    
    #
    # TODO: this needs to be rewritten & abstracted out to higher level choices
    # given the bool flag options and combos. Possibly even adding new methods.
    # For example, if magnitude and stationMag, need to probably query by
    # evid/magid in loop and add contributions to each magnitude. Should
    # probably do the same thing with evid/orid/arrivals and picks.
    # 
    # Convert everything to evid, and use orid as a filter?
    #
    def extract_origin(self, orid, origin=True, magnitude=True, pick=False,
            focalMechanism=False, stationMagnitude=False, anss=False):
        """
        Extract a QML Event from CSS database given an ORID
        """
        event = self.get_event(orid, anss=anss)
        if not event:
            event = self.get_event_from_origin(orid, anss=anss)

        # Should return one origin (given one ORID) 
        if origin:
            _origins = self.get_origins(orid)
            if len(_origins) < 1:
                raise ValueError("No origins for ORID: {0}".format(orid))
            event['type'] = self.converter.origin_event_type(_origins[0])
            event['origin'] = _origins
        if magnitude:
            event['magnitude'] = self.get_magnitudes(orid)
        if pick:
            picks_arrivals = self.get_phases(orid)
            if origin and picks_arrivals:
                _picks, _arrivals = picks_arrivals
                event['pick'] = _picks
                try:
                    event['origin'][0]['arrival'] = _arrivals
                except StandardError as e:
                    pass # log no origin
                # TODO: more stuff -- derive from arrivals, like stationCount, etc
                for o in event.get('origin', []):
                    try:
                        #o['quality'] = in case none yet???
                        o.get('quality', {}).update(qml.get_quality_from_arrival(o['arrival']))
                    except StandardError as e:
                        pass
        if focalMechanism:
            event['focalMechanism'] = self.get_mts(orid) + self.get_focalmechs(orid)
        if stationMagnitude:
            mag_contribs = self.get_station_magnitudes(orid)
            if magnitude and mag_contribs:
                _stamags, _smcontribs = mag_contribs
                event['stationMagnitude'] = _stamags
                # TODO: add stationMagnitudeContribution to magnitudes, same as
                # origin/picks/arrivals...
                get_magid = lambda sid: extract_id(sid).split('-')[-1]
                for mag in event.get('magnitude', []):
                    magid = extract_id(mag['@publicID'])
                    # NOTE: this could be optimized with union sets, just brute it
                    # for correctness so M x N for mags/stamags
                    c = [smc for smc in _smcontribs if magid == get_magid(smc['stationMagnitudeID'])]
                    mag['stationMagnitudeContribution'] = c 
        return event


def get_nearest_place(dsn, coords):
    """
    Return dict of QML nearest_cities given a data source and coordinates
    dsn : str of (database name of places12 schema for now)
    coords : tuple of (x, y)

    Relies on Antelope procedure calls...
    """
    compass = ('N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW')
    wedge = 360./len(compass)
    coord = {'elat': coords[1], 'elon': coords[0]}
    rowopts = {"convert_null": True, "as_dict": True}
    
    dbptr = Database.open(dsn)
    with antds.closing(dbptr):
        db = dbptr.lookup(table='places')
        distances = [db.ex_eval("deg2km(distance({elat}, {elon}, lat, lon))".format(**coord)) for db.record in range(db.record_count)]
        backazis = [db.ex_eval("azimuth(lat, lon, {elat}, {elon})".format(**coord)) for db.record in range(db.record_count)]
        # Find the record with the min distance
        ind = min(xrange(len(distances)), key=distances.__getitem__) 
        dist = distances[ind]
        backazi = backazis[ind]
        fields, rows = Database.get_rows(db, **rowopts)

    minrec = rows[ind]
    shift_azi = (backazi+wedge/2) - (360 * (int(backazi+wedge/2) / 360))
    needle = compass[int(math.floor(shift_azi/wedge))]
    place_info = {'distance': dist, 'direction': needle, 'city': minrec['place'], 'state': minrec['state']}
    s = "{distance:0.1f} km {direction} of {city}, {state}".format(**place_info)
    return s


class Db2Quakeml(object):
    """
    Service to extract info from Antelope Datascope db and convert to QML
    schema. Returns a dict that can be serialized to QuakeML XML using the
    qmlutil.xml.dumps function

    """
    authority_id = "local"
    automatic_authors = []
    agency_id = "XX"
    doi = None
    etype_map = {}
    placesdb = None
    _prefmags = []
    
    logger = logging.getLogger()

    @property
    def preferred_magtypes(self):
        return self._prefmags
    @preferred_magtypes.setter
    def preferred_magtypes(self, mtypes):
        if isinstance(mtypes, str):
            mtypes = mtypes.split(',')
        # TODO: check isinstance iterable
        self._prefmags = mtypes

    def __init__(self, **kwargs):
        """
        Init program with config from keyword args
        """
        for k, v in kwargs.items():
            if k != "run":
                setattr(self, k, v)

        # Make Converter
        self._conv = qml.CSSToQMLConverter(
            agency=self.agency_id, 
            rid_factory=qml.ResourceURIGenerator("quakeml", self.authority_id), 
            utc_factory=qml.timestamp2isostr,
            etype_map=self.etype_map,
            automatic_authors=self.automatic_authors,
        )
    
    def get_deleted_event(self, dsn, orid=None, evid=None, anss=False, **kwargs):
        """
        Return a stub event set to "not existing"

        Notes
        -----
        Maybe not the place for this method, but best place for now
        """
        try:
            dbptr = Database.open(dsn)
            with antds.closing(dbptr):
                db = DatabaseConverter(dbptr, self._conv)
                ev = db.get_event(orid=orid, evid=evid, anss=anss)
            if ev is None:
                raise ValueError("Event not found")
        except Exception as e:
            ev = self._conv.map_event({'evid': evid}, anss=anss)
        finally:
            ev['type'] = "not existing"
        return ev
                
    def get_event(self, dsn, orid=None, evid=None, origin=True, magnitude=True, pick=False,
            focalMechanism=False, stationMagnitude=False, anss=False):
        """
        Run conversion with config
        """
        # IF REGULAR EVENT, USE DATABASE
        ##############################################################################
        # Make db Connection -- wrap in context
        dbptr = Database.open(dsn)
        with antds.closing(dbptr):
            db = DatabaseConverter(dbptr, self._conv)
            ev = db.extract_origin(
                orid, 
                origin=origin, 
                magnitude=magnitude, 
                pick=pick, 
                focalMechanism=focalMechanism,
                stationMagnitude=stationMagnitude,
                anss=anss
            )

        #
        # Set preferreds. The extract method should return in reversed time order, so
        # always choosing the first origin, mag, should be an OK default. Need to use
        # an algorithm for a preferred mag type. For focalmechs, should be mt solutions
        # in reversed time order, then first motions in reveresed time order. This
        # means that a default would be any latest MT, then any latest FM. Or write
        # custom algorithm.
        #
        try:
            ev['preferredOriginID'] = ev['origin'][0]['@publicID']
            ev['preferredMagnitudeID'] = qml.find_preferred_mag(ev['magnitude'][::-1],
                    self.preferred_magtypes)
            if ev.get('focalMechanism'):
                ev['preferredFocalMechanismID'] = ev['focalMechanism'][0]['@publicID']
        except Exception as e:
            self.logger.exception(e)

        #
        # Try the nearest places thing...
        #
        try:
            orig = ev['origin'][0]
            ncd = get_nearest_place(self.placesdb, (orig['longitude']['value'], orig['latitude']['value']))
            desc = self._conv.description(ncd, "nearest cities")
            if isinstance(ev.get('description'), list):
                ev['description'].append(desc)
            else:
                ev['description'] = [desc]
        except Exception as e:
            self.logger.exception(e)
        return ev

    def event2root(self, ev):
        """
        Add event to parameters and root, append evid to publicID
        """
        event_id = ev.get('@publicID', '').split('/', 1)[-1].replace('/', '=')
        catalog = self._conv.event_parameters(event=[ev])
        catalog['@publicID'] += "#{0}".format(event_id)
        if self.doi:
            catalog['creationInfo']['agencyURI'] = "smi:{0}".format(self.doi)
        qmlroot = self._conv.qml(event_parameters=catalog)
        return qmlroot


