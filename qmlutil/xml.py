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
qmlutil.xml

Mark Williams (2015) Nevada Seismological Laboratory

Module to convert QML (QuakeML Modeling Language) structures
to XML (QuakeML) and vice versa

Dumping is easy, assuming you keep the xmltodict syntax in your object.
Loading from file/string is easy for the non-validating parser, but if you
want types, we need to have access to the QuakeML XML schema. This module 
attempts to do this.

Note: Typing is thankfully NOT needed if the application is just creating SQL
statements or anything in HTTP request/responses (except JSON, of course).

"""
import re

from qmlutil.lib import xmltodict

# Module-level dict for XSD -> python type mapping
# - Change xs:dataTime to datetime.datetime.strptime e.g.
# - Maybe make class attribute for flexibility
# TODO: add other legit ones, float, real, etc
XSTYPES = {
    'xs:string': str,
    'xs:integer': int,
    'xs:double': float,
    'xs:boolean': bool,
    'xs:dateTime': str,
    'xs:anyURI': str,
}


def dt(datetime_string):
    """
    Parse datetime string to python datetime.datetime
    """
    raise NotImplementedError("Not done yet")


class TypeExtractor(object):
    """Object to validate/entype XML"""
    XSDtypes = None  # holds flat map of nested elements/XML types
    PYtypes = None   # holds flat map of nested keys/python types
    
    delim = '|'  # Nested key delimiter in type maps
    ns = "bed"   # namespace of XSDtypes keys

    def flatten(self, node, name=""):
        """
        Craete a flat map of XML types from xsd node
        """
        if isinstance(node, dict):
            if '@name' in node:
                #print "Name: {0}, Type: {1}".format(node['@name'], node.get('@type'))
                name += self.delim + node['@name']
                name = name.strip(self.delim)
                if '@type' in node:
                    self.XSDtypes[name] = node['@type']
            if '@base' in node:
                #print "Name: {0}, Base: {1}".format(node.get('@name'), node.get('@base'))
                self.XSDtypes[name] = node['@base']
            
            for n in node:
                #print "Key: {0}".format(n)
                if not n.startswith('@'):
                    self.flatten(node[n], name)
                #else:
                #    print "Attribute: {}, STOPPING".format(n)
        elif isinstance(node, list):
            for n in node:
                self.flatten(n, name)
    
    def __init__(self, qml):
        self.qml = qml
        self.XSDtypes = dict()
        self.PYtypes = dict()
    
    def entype(self, node, name=""):
        """
        Entype the whole dict/list struct under "node" given previously built
        types in self.PYtypes
        
        todo, make deepcopy??
        """
        if isinstance(node, dict):
            for n in node:
                rname = self.delim.join([name, n]).strip(self.delim)
                type_ = self.PYtypes.get(rname)
                if isinstance(node[n], list):
                    for _n in node[n]:
                        self.entype(_n, rname)
                elif isinstance(node[n], dict):
                    self.entype(node[n], rname)
                elif type_:
                    node[n] = type_(node[n])
        return self.qml

    def gentypes(self, node, name="", realname=""):
        """
        Generate flat map of python types for every node in the tree
        
        Map contains python types for given nodes
        Recursively try nested nodes in dict or list
        """
        if isinstance(node, dict):
            # Get new node names based on key
            for n in node:
                keyname = self.delim.join([name, n.lstrip('@')]).strip(self.delim)
                rname = self.delim.join([realname, n]).strip(self.delim)
                self.gentypes(node[n], keyname, rname)
        elif isinstance(node, list):
            # Just pass on node names
            for n in node:
                self.gentypes(n, name, realname)
        else:
            # Try to get a type
            type_ = self._gettype(name)
            if isinstance(type_, str) or isinstance(type_, unicode):
                if type_ in XSTYPES:
                    type_ = XSTYPES[type_]
                elif type_.startswith("bed:"):
                    type_ = self._gettype(type_.lstrip("bed:"))
                    if type_ in XSTYPES:
                        type_ = XSTYPES[type_]
                # Got a code, add to map of python types 
                if isinstance(type_, type):
                    self.PYtypes[realname] = type_
    #
    # TODO: Ugly -- clean this up
    # TODO: use generic settable Ns instead of bed diectly
    #
    def _gettype(self, key):
        """
        Follow the types through linked keys to get a basic type
        """
        type_ = None
        kp = key.split(self.delim)
        if len(kp) <= 2 :
            if key in self.XSDtypes:
                value = self.XSDtypes[key]
                if value.startswith("bed:"):
                    value = self.XSDtypes[value.lstrip("bed:")]
                    type_ = self._gettype(value)
                type_ = value
            else:
                if kp[0] in self.XSDtypes:
                    value = self.XSDtypes[kp[0]].lstrip("bed:")
                    kp[0] = value
                    newkey = self.delim.join(kp)
                    type_ = self._gettype(newkey)
        else:
            if kp[0] in self.XSDtypes:
                value = self.XSDtypes[kp[0]].lstrip("bed:")
                kp[0] = value
                newkey = self.delim.join(kp)
                type_ = self._gettype(newkey)
            elif self.delim.join(kp[:2]) in self.XSDtypes:
                value = self.XSDtypes[self.delim.join(kp[:2])].lstrip("bed:")
                kp = [value] + kp[2:]
                newkey = self.delim.join(kp)
                type_ = self._gettype(newkey)
        return type_

    def extract_typed(self):
        """
        Build type map from data and convert types
        """
        self.gentypes(self.qml)
        return self.entype(self.qml)


class Rounder(object):
    """
    Rounder is an xmltodict preprocessor function for generating NSL QuakeML

    Notes
    -----
    Rounds specified values for objects in an Event because the Client doesn't
    understand precision in computing vs. precision in measurement, or the
    general need for reproducibility in science.
    """
    @staticmethod
    def _round(dict_, k, n):
        """
        Round a number given a dict, a key, and # of places.
        """
        v = dict_.get(k)
        if v is not None:
            v = round(v, n)
            dict_[k] = v
    
    def __init__(self):
        pass

    def __call__(self, k, v):
        # Case of integer attribute
        if k == "nodalPlanes" and v.get("@preferredPlane"):
            v['@preferredPlane'] = str(v['@preferredPlane'])
        
        # USGS can't handle ID in content yet
        if k == "waveformID":
            devnull = v.pop('#text')

        # Don't serialize empty stuff
        if v is None:
            return None
        # Caveat to that is, have to enforce QuakeML rules:
        #
        # arrival: must have phase
        if k == "arrival" and isinstance(v, list):
            v = [p for p in v if p.get('phase') is not None]

        # Round stuff TODO: move to decorator/method
        if k == "depth":
            self._round(v, 'value', -2)
            self._round(v, 'uncertainty', -2)
            # TODO: lowerUncertainty, upperUncertainty, confidenceLevel??
        elif k == "latitude":
            self._round(v, 'uncertainty', 4)
        elif k == "longitude":
            self._round(v, 'uncertainty', 4)
        elif k == "time":
            self._round(v, 'uncertainty', 6)
        elif k == "time":
            self._round(v, 'uncertainty', 6)
        elif k == "originUncertainty":
            self._round(v, 'horizontalUncertainty', -1)
            self._round(v, 'minHorizontalUncertainty', -1)
            self._round(v, 'maxHorizontalUncertainty', -1)
        elif k == "mag":
            self._round(v, 'value', 1)
            self._round(v, 'uncertainty', 2)
        return k, v
            

class SimpleTyping(object):
    """
    Postprocessor for xmltodict that will ID basic python types. This is wild
    west YAML-style, if it looks like a number, it is.
    """
    # TODO: add types as additional struct/class
    IS_FLOAT = re.compile(r"[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?")
        
    # TODO: add time, make optional templates???
    
    def __init__(self, *args, **kwargs):
        # TODO: construct things like (type_, regex) tuples to loop through and
        # pass in call, do in init to avoid overhead.
        pass

    def __call__(self, path, k, v):
        # Ignore if supposed to be string for now
        # NOTE: attribs and cdata can be changed...
        if k.startswith('@') or k == "#text":
            return (k, v)
        
        # NOTE: fails on times???
        try:
            if v.isdigit():
                v = int(v)
            elif self.IS_FLOAT.match(v):
                v = float(v)
        except Exception as e:
            # log
            pass
        return (k, v)


def ignore_null(k, v):
    """
    Preprocessor for xmltodict.unpasre that ignores keys with None value
    """
    if v is None:
        return None
    return k, v


def dumps(input_dict, *args, **kwargs):
    """
    Dump QML dict object to XML string
    """
    return xmltodict.unparse(input_dict, *args, **kwargs)

# TODO: add kwargs for typing/conversions???
#
def loads(xml_input, *args, **kwargs):
    """Load QML dict object from XML"""
    return xmltodict.parse(xml_input, *args, **kwargs)

# Testing
def main():
    with open('data/QuakeML-BED-1.2.xsd') as f:
        schema = loads(f)

    with open('tests/quakeml.xml') as f:
        qroot = loads(f)
    qml = qroot['q:quakeml']

    te = TypeExtractor(qml) # extractor set with qml pulled from xmltodict
    te.flatten(schema)  # build type schema map from xsd pulled from xmltodict
    # 
    q = te.extract_typed()
    return q, te, schema

# Run test
#q, te, schema = main()

