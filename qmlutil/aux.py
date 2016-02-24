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

