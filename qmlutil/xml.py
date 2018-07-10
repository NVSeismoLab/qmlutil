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

This mostly contains helper functions in the form of pre/post-processors which
can be passed to xmltodict to control the (de)serialization process.

Simple types can be done with a regex on the value. For strict QuakeML typing,
we need to parse the schema and use the path of each item. This module
currently does NOT have that capability.

"""
import re

from qmlutil.lib import xmltodict

# Types from xs to python used by QuakeML schema
# NOTE: not used, not done.
XSTYPES_PYTHON = {
    'xs:string': str,
    'xs:integer': int,
    'xs:double': float,
    'xs:boolean': bool,
    'xs:dateTime': str,
    'xs:anyURI': str,
}

#
# PREPROCESSORS
# -------------
# Functions for xmltodict.unparse (dumps)
#

def ignore_null(k, v):
    """
    Preprocessor for xmltodict.unparse that ignores keys with None value
    """
    if v is None:
        return None
    return k, v


class Rounder(object):
    """
    Rounder is an xmltodict.unparse preprocessor function for generating NSL QuakeML

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
        elif k == "originUncertainty":
            self._round(v, 'horizontalUncertainty', -1)
            self._round(v, 'minHorizontalUncertainty', -1)
            self._round(v, 'maxHorizontalUncertainty', -1)
        elif k == "mag":
            self._round(v, 'value', 1)
            self._round(v, 'uncertainty', 2)
        return k, v
            

#
# POSTPROCESSORS
# --------------
# Functions for xmltodict.parse (loads)
#

class SimpleTyping(object):
    """
    Postprocessor for xmltodict.parse that will ID basic python types. This is wild
    west YAML-style, if it looks like a number, it is.

    Types are REGEXs that run in order, first match will entype and return.

    Use like:
        d = loads(my_xml, postprocessor=SimpleTyping())
    """
    regex_types = [
        # INT
        (re.compile(r"[-+]?\d+"), int),
        # FLOAT
        (re.compile(r"[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"), float),
    ]
    
    skip_keys = set()

    def __init__(self, *args, **kwargs):
        # TODO: allow appending args of re.compiled regex, type_ tuples to the
        # class list as init?
        pass # possibly allow initing attrib or cdata customs

    def __call__(self, path, k, v):
        # Ignore if supposed to be string for now, in XML attrib should always
        # be quoted, so just assume strings.
        # NOTE: attribs and cdata can be changed...
        if k.startswith('@') or k == "#text" or k in self.skip_keys:
            return (k, v)
        
        # Try every regex and type it if match
        # NOTE: fails on times???
        for exp, type_ in self.regex_types:
            try:
                if exp.match(v):
                    v = type_(v)
                    return (k, v)
            except Exception as e:
                pass # log
        return (k, v)


def dumps(input_dict, *args, **kwargs):
    """
    Dump QML dict object to XML string
    """
    return xmltodict.unparse(input_dict, *args, **kwargs)


def loads(xml_input, *args, **kwargs):
    """Load QML dict object from XML"""
    return xmltodict.parse(xml_input, *args, **kwargs)


