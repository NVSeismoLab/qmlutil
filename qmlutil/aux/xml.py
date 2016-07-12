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
Auxiliary utilities for QuakeML

These have 3rd party deps that are not shipped with qmlutil

"""
from qmlutil import data as metadata

VALIDATION_SCHEMAS = {
    "BED": metadata.QUAKEML_12_RELAXNG,
    "BED-RT": metadata.QUAKEML_RT_12_RELAXNG,
}

def validate(f, schema="BED"):
    """
    Validate a QuakeML file using a given RelaxNG schema
    """
    from lxml import etree

    # Load schema
    schemafile = VALIDATION_SCHEMAS[schema]
    schema = etree.parse(schemafile)
    rng = etree.RelaxNG(schema)
    
    # Load QuakeML
    if isinstance(f, file):
        qml = etree.parse(f)
    elif isinstance(f, unicode):
        qml = etree.fromstring(f.encode())
    elif isinstance(f, str):
        qml = etree.fromstring(f)

    is_valid = rng.validate(qml)
    return is_valid


def main():
    import sys
    filename = sys.argv[1]
    ok = validate(filename)
    print "{0} is valid?: {1}".format(filename, ok)
    sys.exit(0)


