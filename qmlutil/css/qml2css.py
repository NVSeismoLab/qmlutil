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
qmlutil.css.qml2css

NOT FINISHED - IN PROGRESS
"""

class Counter(object):
    """
    Singleton counter as default ID generator

    Should be a custom factory defined by user. This isn't safe for most
    applications, but ok for testing/GIL ops.
    """
    _id = {}
    
    @classmethod
    def set(cls, ns, value):
        """Set a starting integer for a namespace"""
        cls._id[ns] = value

    @classmethod
    def newint(cls, ns):
        """Return a new integer ID given a namespace"""
        if ns in cls._id:
            cls._id[ns] += 1
        else:
            cls._id[ns] = 0
        return cls._id[ns]


def dget(dict_, keys, delim=':'):
    """
    Delimited dict get - Recursive get function for nested dicts

    Recursive 'get' method for format: 'key1:key2' for d[key1][key2]
    
    keys : delimited string OR sequence of keys
    delim : string of delimiter [':']
    """
    if isinstance(keys, str):
        keys = keys.split(delim)
    try:
        for k in keys:
            dict_ = dict_[k]
    except KeyError:
        return None
    return dict_


def delimited_getter(delim=':'):
    """Closure delimited function version of dget"""
    def _getter(dict_, keys):
        return dget(dict_, keys, delim)
    return _getter


def dset(dict_, keys, value, delim=':'):
    """Delimited nested dict setter"""
    d = dict_
    if isinstance(keys, str):
        keys = keys.split(delim)
    try:
        for k in keys[:-1]:
            d = d[k]
    except KeyError:
        d = None
    if d is not None:
        d[keys[-1]] = value


def delimited_setter(delim=':'):
    """Closure delimited function version of dset"""
    def _setter(dict_, keys, value):
        return dset(dict_, keys, value, delim)
    return _setter


class Delimiter(object):
    """Class of delimitter with both getter and setter"""
    _d = ':'

    @property
    def delimiter(self):
        return self._d
    
    @delimiter.setter
    def delimiter(self, value):
        self._d = value
        self.get = delimited_getter(self.delimiter)
        self.set = delimited_setter(self.delimiter)

    def __init__(self, delimiter=None):
        if delimiter:
            self.delimiter = delimiter


D = Delimiter('|')

#
# TODO: typing... either use QuakeML types only, maybe push CSS typing up to 
# Antelope level?
#
class QMLToCSSConverter(object):
    """
    """
    css = dict()  # Top level set of tables
    id_factory = Counter.newint

    def newid(self, ns):
        return self.id_factory(ns)

    def _map_arrival(self, a):
        pass

    def _map_pick(self, p):
        pass

    def _map_magnitude(self, m):
        pass

    def _map_focalmech(self, fm):
        pass
    
    # TODO: - handle lddate convert to timestamp etc
    #       - pull author etc from creationInfo
    def _map_origin(self, o):
        """
        Map QuakeML origin to CSS tables
        """
        origin = dict(
            lat = D.get(o, 'latitude|value'), 
            lon = D.get(o, 'longitude|value'), 
            depth = D.get(o, 'depth|value'), 
            time = D.get(o, 'time|value'), 
            nass = D.get(o, 'quality|associatedPhaseCount'), 
            ndef = D.get(o, 'quality|usedPhaseCount'), 
        )
        
        # TODO: check if horizontal uncertainty exists?
        # NOTE: There can be more than 1 uncertainty. Right now this code will
        # just return a None if that happens, b/c the get will fail on a list.
        origerr = dict(
            sdobs = D.get(o, 'quality|standardError'),
            stime = D.get(o, 'time|uncertainty'),
            sdepth = D.get(o, 'depth|uncertainty'),  # TODO: m2km
            smajax = D.get(o, 'originUncertainty|maxHorizonalUncertainty'), # TODO: m2km
            sminax = D.get(o, 'originUncertainty|minHorizonalUncertainty'), # TODO: m2km
            strike = D.get(o, 'originUncertainty|azimuthMaxHorizonalUncertainty'),
            conf = D.get(o, 'originUncertainty|confidenceLevel'), # TODO: convert from percentage to decimal
        )

        if 'arrival' in o and isinstance(o, list):
            # map mostly assoc values here, I believe...
            # assoc = [self._map_arrival(a) for a in o['arrival']]
            pass

        css = dict(
            origin = origin,
            origerr = origerr,
            assoc = assoc,
        )
        return css

    def _map_event(self, e):
        pass

    def _map_catalog(self, c):
        pass



