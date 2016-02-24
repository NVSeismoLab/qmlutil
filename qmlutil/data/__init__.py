#
"""
qmlutil.data

metadata shortcuts for the non-python data in the data folder
"""
import os

DATADIR = os.path.dirname(__file__)

QUAKEML_12_RELAXNG = os.path.join(DATADIR, "QuakeML-1.2.rng")
QUAKEML_BED_12_RELAXNG = os.path.join(DATADIR, "QuakeML-BED-1.2.rng")
QUAKEML_RT_12_RELAXNG = os.path.join(DATADIR, "QuakeML-RT-1.2.rng")
QUAKEML_BEDRT_12_RELAXNG = os.path.join(DATADIR, "QuakeML-RT-BED-1.2.rng")
QUAKEML_BED_12_XSD = os.path.join(DATADIR, "QuakeML-BED-1.2.xsd")
QUAKEML_BEDRT_12_XSD = os.path.join(DATADIR, "QuakeML-RT-BED-1.2.xsd")


