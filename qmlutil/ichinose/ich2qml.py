# -*- coding: utf-8 -*-
"""
# ichinose.py
# -by Mark (2013), Nevada Seismological Laboratory
# NSL Ichinose file Parser class
#
# contains class and fxns to make an ObsPy event
# from Gene Ichinose's moment tensor text output
# (specifically optimized for 'moment.php' files
# for now...
#
# Parser -> class which holds text and methods
#            to extract certain values of the mt inversion
#
"""
import datetime
import re
import uuid

from qmlutil import Dict, Root, ResourceURIGenerator, rfc3339, anss_params

TIMEFMT = '%Y-%m-%dT%H:%M:%S'

def _km2m(dist):
    """Convert from km to m only if dist is not None"""
    if dist is not None:
        return dist * 1000.
    else:
        return None


def _quan(*args, **kwargs):
    """
    Return a dict only if the value for key "value" is not None
    """
    dict_ = Dict(*args, **kwargs)
    if dict_.get('value') is None:
        return None
    return dict_


def _dt2str(dt):
    if dt is not None:
        return rfc3339(dt)


class Parser(object):
    '''
    Parse the NSL Icinose email output 

    '''
    line = []

    def __init__(self, email_text, endline="\n"):
        '''
        Working data is a list of lines from the file
        '''
        if isinstance(email_text, file):
            email_text = email_text.read()
        self.line = email_text.split(endline)
    
    def _id(self, n):
        '''Pull out an integer ID'''
        return int(self.line[n].split(':')[-1])

    def _event_info(self, n):
        '''Pull out date/time lat lon from info line'''
        date, julday, time, lat, lon, orid = self.line[n].split()
        date = date.replace('/','-')
        utctime = datetime.datetime.strptime('T'.join([date,time]), TIMEFMT + '.%f')
        latitude = float(lat)
        longitude = float(lon)
        orid = int(orid)
        return {'time': utctime, 'lat': latitude, 'lon': longitude, 'orid': orid }
        
    def _depth(self, n):
        '''Stub'''
        depth = re.findall('\d+\.\d+', self.line[n])[0]
        return float(depth)

    def _mt_sphere(self, n):
        '''
        Moment Tensor in Spherical coordinates
        Input  :  n (where n is line of title)
        Output :  dict of element/value of tensor
                  e.g. 'Mrr','Mtf' raised to 'EXP'-7 (N-m)
        '''
        line1  =  re.findall(r'...=(?:\s+\-?\d\.\d+|\d{2})', self.line[n+1])
        line1  += re.findall(r'...=(?:\s+\-?\d\.\d+|\d{2})', self.line[n+2])
        exp_str = line1.pop(-1)
        exp = int(exp_str.split('=')[1]) - 7 # N-m
        mt = dict(m.split('=') for m in line1)
        for k, v in mt.items():
            mt[k] = float(v) * 10**exp
        return mt

    def _mt_cart(self, n):
        '''
        Moment Tensor in Cartesian coordinates

        Take the three lines after n and build a 3x3 list of lists
        '''
        m = []
        for l in range(n+1,n+4):
            m.append([float(x) for x in self.line[l].split()])
        return m

    def _vectors(self, n):
        '''
        Return info on eigenvalues/vectors of princial axes (P,T,N)
        '''
        axes = {}
        for l in range(n+1,n+4):
            axis = {}
            name = re.findall(r'.\-axis', self.line[l])[0][0]
            ax_values = re.findall(r'\w+=(?:\s?\-?\d+\.\d+|\d+)', self.line[l])
            for _a in ax_values:
                key, value = _a.split('=')
                value = float(value)
                axis[key] = value
            axes[name] = axis
        return axes

    def _gap(self, n):
        gap_exp, dist_exp = re.findall(r'\w+=\s*(?:\d+\.\d+|\d+)', self.line[n])
        gap  = gap_exp.split('=')[-1]
        dist = dist_exp.split('=')[-1]
        return float(gap)

    def _percent(self, n):
        perc = re.findall(r'(?:\d+\.\d+|\d+)\s?%',self.line[n])[0].split()[0]
        frac = float(perc)/100.
        return frac
    
    def _epsilon(self, n):
        '''Pull out epsilon variance'''
        return float(self.line[n].split('=')[-1])

    def _mw(self, n):
        return float(self.line[n].split()[-1])

    def _mo(self, n):
        '''
        Pull out scalar moment
        Output in N-m
        '''
        str_mo = re.findall(r'\d+\.\d+x10\^\d+', self.line[n])[0]
        str_mo = re.split(r'[x\^]',str_mo)
        mant = float(str_mo[0])
        bse  = int(str_mo[1])
        exp  = int(str_mo[2])
        exp -= 7 # convert from dyne-cm to Nm
        return mant*bse**exp

    def _double_couple(self, n):
        '''
        Line 'n' is line 'Major Double Couple'
        Return list of 2 [strike,dip,rake] lists of plane values
        '''
        values1 = self.line[n+2].split(':')[-1]
        values2 = self.line[n+3].split(':')[-1]
        plane1  = [float(x) for x in values1.split()]
        plane2  = [float(x) for x in values2.split()]
        return [plane1, plane2]
    
    def _number_of_stations(self, n):
        '''
        Extracts number of defining stations used
        '''
        ns = re.findall(r'Used=\d+', self.line[n])[0]
        return int(ns.split('=')[-1])

    def _creation_time(self, n):
        '''
        When file says it was made
        '''
        label, date, time = self.line[n].split()
        date = date.replace('/','-')
        return datetime.datetime.strptime('T'.join([date,time]), TIMEFMT)

    def run(self):
        """
        In future, parse the file and have attributes available
        """
        p = self
        ichi = Dict()
        
        # Maybe get rid of all this stuff...
        event         = Dict(event_type='earthquake')
        origin        = Dict()
        focal_mech    = Dict()
        nodal_planes  = Dict()
        moment_tensor = Dict()
        principal_ax  = Dict()
        magnitude     = Dict()
        data_used     = Dict()
        creation_info = Dict()

        ichi['mode'] = 'automatic'
        ichi['status'] = 'preliminary'
        # Parse the entire file line by line.
        for n,l in enumerate(p.line):
            if 'REVIEWED BY NSL STAFF' in l:
                ichi['mode'] = 'manual'
                ichi['status'] = 'reviewed'
            if 'Event ID' in l:
                ichi['evid'] = p._id(n)
            if 'Origin ID' in l:
                ichi['orid'] = p._id(n)
            if 'Ichinose' in l:
                ichi['category'] = 'regional'
            if re.match(r'^\d{4}\/\d{2}\/\d{2}', l):
                ichi['event_info'] = p._event_info(n)
            if 'Depth' in l:
                ichi['derived_depth'] = p._depth(n)
            if 'Mw' in l:
                ichi['mag'] = p._mw(n) 
                ichi['magtype'] = 'Mw'
            if 'Mo' in l and 'dyne' in l:
                ichi['scalar_moment'] = p._mo(n)
            if 'Percent Double Couple' in l:
                ichi['double_couple'] = p._percent(n)
            if 'Percent CLVD' in l:
                ichi['clvd'] = p._percent(n)
            if 'Epsilon' in l:
                ichi['variance'] = p._epsilon(n)
            if 'Percent Variance Reduction' in l:
                ichi['variance_reduction'] = p._percent(n)
            if 'Major Double Couple' in l and 'strike' in p.line[n+1]:
                np = p._double_couple(n)

                ichi['nodal_planes'] = Dict([
                    ('nodalPlane1', Dict([
                        ('strike', Dict(value = np[0][0])),
                        ('dip', Dict(value = np[0][1])),
                        ('rake', Dict(value = np[0][2])),
                        ])
                    ),
                    ('nodalPlane2', Dict([
                        ('strike', Dict(value = np[1][0])),
                        ('dip', Dict(value = np[1][1])),
                        ('rake', Dict(value = np[1][2])),
                        ])
                    ),
                    ('@preferredPlane', 1),
                ])
            if 'Spherical Coordinates' in l:
                mt = p._mt_sphere(n)
                
                ichi['tensor'] = Dict([
                    ('Mrr', Dict(value=mt.get('Mrr'))),
                    ('Mtt', Dict(value=mt.get('Mtt'))),
                    ('Mpp', Dict(value=mt.get('Mff'))),
                    ('Mrt', Dict(value=mt.get('Mrt'))),
                    ('Mrp', Dict(value=mt.get('Mrf'))),
                    ('Mtp', Dict(value=mt.get('Mtf'))),
                ])
            if 'Eigenvalues and eigenvectors of the Major Double Couple' in l:
                ax = p._vectors(n)
                t_axis = (ax['T']['trend'], ax['T']['plunge'], ax['T']['ev'])
                p_axis = (ax['P']['trend'], ax['P']['plunge'], ax['P']['ev'])
                n_axis = (ax['N']['trend'], ax['N']['plunge'], ax['N']['ev'])
                
                ichi['principal_axes'] = Dict([
                    ('tAxis', Dict([
                        ('azimuth', Dict(value = t_axis[0])),
                        ('plunge', Dict(value = t_axis[1])),
                        ('length', Dict(value = t_axis[2])),
                        ])
                    ),
                    ('pAxis', Dict([
                        ('azimuth', Dict(value = p_axis[0])),
                        ('plunge', Dict(value = p_axis[1])),
                        ('length', Dict(value = p_axis[2])),
                        ])
                    ),
                    ('nAxis', Dict([
                        ('azimuth', Dict(value = n_axis[0])),
                        ('plunge', Dict(value = n_axis[1])),
                        ('length', Dict(value = n_axis[2])),
                        ])
                    ),
                ])
            if 'Number of Stations' in l:
                ichi['data_used_station_count'] = p._number_of_stations(n)
            if 'Maximum' in l and 'Gap' in l:
                ichi['azimuthal_gap'] = p._gap(n)
            if re.match(r'^Date', l):
                ichi['creation_time'] = p._creation_time(n)
        return ichi 


class IchinoseToQmlConverter(Root):
    """
    Convert Ichinose
    """
    event = None
    parser = None

    def __init__(self, fh, *args, **kwargs):
        """
        Set event
        """
        self.parser = Parser(fh)
        super(IchinoseToQmlConverter, self).__init__(*args, **kwargs) 
         
    def get_event(self, anss=False):
        """
        Build an obspy moment tensor focal mech event

        This makes the tensor output into an Event containing:
        1) a FocalMechanism with a MomentTensor, NodalPlanes, and PrincipalAxes
        2) a Magnitude of the Mw from the Tensor

        Which is what we want for outputting QuakeML using
        the (slightly modified) obspy code.

        Input
        -----
        filehandle => open file OR str from filehandle.read()

        Output
        ------
        event => instance of Event() class as described above
        """
        # Get best creation time you can
        ichi = self.parser.run()
        hypo = ichi.get('event_info', {})
        evid = ichi.get('evid')
        orid = ichi.get('orid')
        dt = ichi.get('creation_time') or datetime.datetime.utcnow()
        ustamp = int((dt-datetime.datetime(1970, 01, 01, 00, 00, 00)).total_seconds())
        vers = "{0}-{1}-{2}".format(evid, orid, ustamp)
        ichiID_rid = "{0}/{1}".format('ichinose', vers) # TODO: format/errcheck
        originID_rid = "{0}/{1}".format('origin', orid or uuid.uuid4())
        eventID_rid = "{0}/{1}".format('event', evid)
        
        origin = Dict([
            ('@publicID', self._uri(ichiID_rid, local_id="origin")),
            ('latitude', _quan([
                ('value', hypo.get('lat')),
                ])
            ),
            ('longitude', _quan([
                ('value', hypo.get('lon')),
                ])
            ),
            ('depth', _quan([
                ('value', _km2m(ichi.get('derived_depth'))),
                ]),
            ),
            ('time', _quan([
                ('value', _dt2str(hypo.get('time'))),
                ]),
            ),
            ('depthType', "from moment tensor inversion"),
            ('evaluationMode', ichi.get('mode')),
            ('evaluationStatus', ichi.get('status')),
            ('creationInfo', Dict([
                ('creationTime', _dt2str(ichi.get('creation_time'))),
                ('version', vers),
                ])
            ),
        ])

        magnitude = Dict([
            ('@publicID', self._uri(ichiID_rid, local_id="mag")),
            ('mag', Dict(value=ichi.get('mag'))),
            ('type', ichi.get('magtype')),
            ('evaluationMode', ichi.get('mode')),
            ('evaluationStatus', ichi.get('status')),
            ('creationInfo', Dict([
                ('creationTime', _dt2str(ichi.get('creation_time'))),
                ('version', vers)
                ])
            ),
        ])
        
        moment_tensor = Dict([
            ('@publicID', self._uri(ichiID_rid, local_id="mt")),
            ('derivedOriginID', self._uri(ichiID_rid, local_id="origin")),
            ('scalarMoment', Dict(value=ichi.get('scalar_moment'))),
            ('doubleCouple', ichi.get('double_couple')),
            ('tensor', ichi.get('tensor')),
            ('category', "regional"),
            ('dataUsed', Dict([
                ('waveType', "combined"),
                ('stationCount', ichi.get('data_used_station_count')),
                ])
            ),
            ('creationInfo', Dict([
                ('creationTime', _dt2str(ichi.get('creation_time'))),
                ('version', vers),
                ])
            ),
        ])
        
        focal_mechanism = Dict([
            ('@publicID', self._uri(ichiID_rid, local_id="focalmech")),
            ('triggeringOriginID', self._uri(originID_rid)),
            ('nodalPlanes', ichi.get('nodal_planes')),
            ('principalAxes', ichi.get('principal_axes')),
            ('momentTensor', moment_tensor),
            ('creationInfo', Dict([
                ('creationTime', _dt2str(ichi.get('creation_time'))),
                ('version', vers),
                ])
            ),
            ('evaluationMode', ichi.get('mode')),
            ('evaluationStatus', ichi.get('status')),
        ])
        
        event = Dict([
            ('@publicID', self._uri(eventID_rid)),
            ('focalMechanism', [focal_mechanism]),
            ('magnitude', [magnitude]),
            ('origin', [origin]),
            ('preferredMagnitudeID', magnitude.get('@publicID')),
            ('preferredFocalMechanismID', focal_mechanism.get('@publicID')),
            ('creationInfo', Dict([
                ('creationTime', _dt2str(ichi.get('creation_time'))),
                ('version', str(evid)),
                ])
            ),
        ])
        if anss:
            event.update(anss_params(self.agency, evid))
        return event
        

def mt2event(filehandle, rid_factory=None, agency=None, anss=False):
    """
    Return an Event from an Ichinose MT text file
    """
    return IchinoseToQmlConverter(filehandle,
        rid_factory=rid_factory, agency=agency).get_event(anss=anss)


