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
import math
import logging

from curds2.dbapi2 import connect
from curds2.rows import OrderedDictRow

import qmlutil as qml
from qmlutil.css import extract_id

class DatabaseConverter(object):
    """
    Convert to QML given an Antelope database Connection

    Methods take an ORID, return QML elements/types
    """
    connection = None  # DBAPI2 standard connection
    converter = None # converter class

    def __init__(self, connection, converter):
        self.connection = connection
        self.converter = converter
        
        self.connection.row_factory = OrderedDictRow
        self.connection.CONVERT_NULL = True
    
    def _evid(self, orid):
        """
        Get EVID from ORID
        """
        cmd = ['dbopen origin', 'dbsubset orid=={0}'.format(orid), 'dbsort lddate']
        curs = self.connection.cursor()
        rec = curs.execute('process', [cmd])
        if rec:
            return curs.fetchone().get('evid')

    def get_event(self, orid=None, evid=None, anss=False):
        if orid and not evid:
            evid = self._evid(orid)
        cmd = ['dbopen event', 'dbsubset evid=={0}'.format(evid)]
        curs = self.connection.cursor()
        rec = curs.execute('process', [cmd])
        if rec:
            ev = curs.fetchone()
            return self.converter.map_event(ev, anss=anss)
    
    def get_event_from_origin(self, orid=None, anss=False):
        """
        Get event from origin table (in case no event/prefor)
        """
        cmd = ['dbopen origin', 'dbsubset orid=={0}'.format(orid)]
        curs = self.connection.cursor()
        rec = curs.execute('process', [cmd])
        if rec:
            ev = curs.fetchone()
            return self.converter.map_event(ev, anss=anss)

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
        curs = self.connection.cursor()
        rec = curs.execute('process', [cmd] )
        curs.CONVERT_NULL = False  # Antelope schema bug - missing fplane NULLS
        return self.converter.convert_focalmechs(curs, "fplane")
    
    def get_mts(self, orid=None):
        """
        Returns FocalMechanism instances or ORID from mt table
        """
        cmd = ['dbopen mt', 'dbsubset orid=={0}'.format(orid), 
            'dbsort -r lddate']
        curs = self.connection.cursor()
        rec = curs.execute('process', [cmd] )
        return self.converter.convert_focalmechs(curs, "mt")

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
        curs = self.connection.cursor()
        rec = curs.execute('process', [cmd] )
        return self.converter.convert_origins(curs)
    
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
        curs = self.connection.cursor()
        rec = curs.execute('process', [('dbopen netmag', substr, 'dbsort -r lddate')] )
        if rec:
            mags += [self.converter.map_netmag2magnitude(db) for db in curs]
            return mags

        # 2. Check the origin table for the 3 types it holds
        curs = self.connection.cursor()
        rec = curs.execute('process', [('dbopen origin', substr)] )
        if rec:
            db = curs.fetchone()
            mags += [self.converter.map_origin2magnitude(db, mtype=mtype) 
                     for mtype in ('ml', 'mb', 'ms') if db.get(mtype)]
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
        curs = self.connection.cursor()
        rec = curs.execute('process', [cmd])
        return self.converter.convert_magnitudes(curs)

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
        curs = self.connection.cursor()
        rec = curs.execute('process', [cmd] )
        return self.converter.convert_phases(curs)
    
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

    with connect(dsn, row_factory=OrderedDictRow, CONVERT_NULL=True) as conn:
        coord = {'elat': coords[1], 'elon': coords[0]}
        curs = conn.cursor()
        n = curs.execute.lookup(table='places')
        distances = [curs.execute.ex_eval("deg2km(distance({elat}, {elon}, lat, lon))".format(**coord)) for curs._record in range(curs.rowcount)]
        backazis = [curs.execute.ex_eval("azimuth(lat, lon, {elat}, {elon})".format(**coord)) for curs._record in range(curs.rowcount)]
        # Find the record with the min distance
        ind = min(xrange(len(distances)), key=distances.__getitem__) 
        dist = distances[ind]
        backazi = backazis[ind]
        curs.scroll(int(ind), 'absolute')
        minrec = curs.fetchone()
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
            with connect(dsn) as conn:
                db = DatabaseConverter(conn, self._conv)
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
        #with connect(dsn, row_factory=OrderedDictRow, CONVERT_NULL=True) as conn:
        with connect(dsn) as conn:
            db = DatabaseConverter(conn, self._conv)
            ev = db.extract_origin(orid, 
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


