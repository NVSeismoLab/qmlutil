qmlutil
=======
Utilities for QuakeML

In a perfect world, all professional seismological applications speak QuakeML. This is for when that doesn't happen.

About
-----
This is the Nevada Seismological Lab's python package for dealing with "QML", the QuakeML Model Language schema. It mostly contains housekeeping classes and functions for dealing with python dicts and lists adhering to the QuakeML v1.2 schema. It contains some schema converter classes, and a few plugins for using 3rd party libraries.

This module is a work-in-progress, and may change until a 1.0 release. That said, the goal is to keep the current methods and API stable up to and through the 1.0. NSL is currently using this lib in production, so it behooves us not to change the API as much as possible. More/better doc to come, hopefully.

NSL builds all python libraries as wheels; to build qmlutil, clone the repo and build an installable wheel in the top-level directory:
```shell
% git clone https://github.com/NVSeismoLab/qmlutil
% pip wheel -w /tmp ./
```

Philosophy
----------
This module aims to:
* be written in pure python
* have zero (or minimal) dependencies
* prefer python data structures over classes

Rather than map classes to classes, and have to write custom JSON, XML, etc encoders, this module attempts to do schema translation using python dicts, lists, etc as fundamental units of records, rows, and documents. There are many good existing implementations of QuakeML classes, including those distributed by quakeml.org, and the excellent ObsPy framework. Those or other custom classes can easily be built using the structures from this module. Being in pure python allows this lib to be used by other interpreters, i.e. pypy. Another goal of this project is to produce structures which can easily be serialized to other wire formats, i.e. JSON, msgpack, Avro, or Protocol Buffers.

The core of this module has no external dependencies. Serialization to XML is done through the `xmltodict` module, which is included in this package. There are plugins (currently named the `aux` module), which do have external dependencies. For instance, serialization to XML is pure python, but the XSD schema validator currently depends on the `lxml` package (validating is highly recommended in production).

Description
-----------
Core
* `qmlutil.css` - Convert between CSS3.0 and QML1.2 schemas (currently only CSS->QML)
* `qmlutil.ichinose` - Convert Ichinose moment tensor text output to QML1.2
* `qmlutil.lib` - Contains vendored packages
* `qmlutil.xml` - Serialize a python QML structure (dicts + lists) to XML/QuakeML
Require other python libs
* `qmlutil.aux.antelope` - Contains converter classes for Antelope CSS databases
* `qmlutil.aux.xml` - Contains classes for more advanced XML tasks that require libxml2

Dependencies
------------
There are no deps for core. The `aux` (change name to `plugins`) modules have various vendor reqs:
* The `antelope` plugin requires the proprietary `antelope` packages and NSL's `curds2` DBAPI driver
* The `xml` plugin requires the `lxml` package

License
-------
Copyright 2016 University of Nevada, Reno

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

