# -*- coding: utf-8 -*-
"""
Core/common for qmlutil packages

Mark C. Williams (2016)
Nevada Seismological Lab

"""

import datetime

# Time format for string
RFC3339 = '%Y-%m-%dT%H:%M:%S.%fZ'

def _dt(timestamp):
    """Returns the UTC dateTime"""
    try:
        return datetime.datetime.utcfromtimestamp(timestamp)
    except:
      return None


def rfc3339(dt):
    """
    Format datetime in ISO8601
    """
    return dt.strftime(RFC3339)
    

def timestamp2isostr(timestamp):
    """
    Returns float epoch timestamp in RFC3339-ISO8601

    Note
    ----
    This is python wrapper middleware (fails silently)
    """
    try:
        return rfc3339(_dt(timestamp))
    except:
      return None


class ResourceURIGenerator(object):
    """
    Create function to generate URI's for QuakeML
    """
    _pattern = r"(smi|quakeml):[\w\d][\w\d\−\.\∗\(\)_~’]{2,}/[\w\d\−\.\∗\(\)_~’][\w\d\−\.\∗\(\)\+\?_~’=,;#/&amp;]∗" 
    schema = None
    authority_id = None

    def __init__(self, schema="smi", authority_id="local"):
        self.schema = schema
        self.authority_id = authority_id

    def __call__(self, resource_id=None, local_id=None, authority_id=None, schema=None):
        """
        Generate an id, given a resource-id and possible local-id, other parts
        can be overridden here as well
        """
        if not resource_id:
            resource_id = str(uuid.uuid4())
        schema = schema or self.schema
        auth_id = authority_id or self.authority_id
        rid = "{0}:{1}/{2}".format(schema, auth_id, resource_id)
        if local_id:
            rid += "#{0}".format(local_id)
        return rid

    def validate(rid):
        """Validate"""
        raise NotImplementedError("Not done yet")


