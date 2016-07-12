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
qmlutil - Utilities for working with QuakeML

Mark C. Williams (2015)
Nevada Seismological Laboratory

QuakeML helper functions, classes and variables for conversion

In a perfect world, all seismological applications speak QuakeML. This is for
when that doesn't happen.

"""
from qmlutil.core import (Root, ResourceURIGenerator, timestamp2isostr,
    rfc3339, find_preferred_mag, get_preferred, anss_params, Dict,
    station_count, get_quality_from_arrival)
from qmlutil.css import CSSToQMLConverter, extract_etype
from qmlutil.ichinose import IchinoseToQmlConverter, mt2event
from qmlutil.xml import dumps, ignore_null, Rounder


