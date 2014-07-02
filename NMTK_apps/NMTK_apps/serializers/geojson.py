#!/usr/bin/env python
# Non-Motorized Toolkit
# Copyright (c) 2014 Open Technology Group Inc. (A North Carolina Corporation)
# Developed under Federal Highway Administration (FHWA) Contracts:
# DTFH61-12-P-00147 and DTFH61-14-P-00108
# 
# Redistribution and use in source and binary forms, with or without modification, 
# are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright notice, 
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright 
#       notice, this list of conditions and the following disclaimer 
#       in the documentation and/or other materials provided with the distribution.
#     * Neither the name of the Open Technology Group, the name of the 
#       Federal Highway Administration (FHWA), nor the names of any 
#       other contributors may be used to endorse or promote products 
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL 
# Open Technology Group Inc BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT 
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF 
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED 
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT 
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
Created on 2011-05-12
Updated on 2011-11-09 -- added desrializer support

@author: Daniel Sokolowski

Extends django's built in JSON serializer to support GEOJSON encoding

Requirements:
    Install and setup geodjango (django.contrib.gis)

Install:
    Add ``SERIALIZATION_MODULES = { 'geojson' : 'path.to.geojson_serializer' }`` to your 
    project ``settings.py`` file.
    
Usage:
    from django.core import serializers
    geojson = serializers.serialize("geojson", <Model>.objects.all())
    
Console Usage: 
    python manage.py dumpdata advertisements.advertiserlocation --format geojson --indent 4 --settings=settings_dev > fixture.geojson
         --- check the file and verify that no extra characters were added at top and end of the dump
    python manage.py loaddata fixture.geojson --settings=settings_dev
    
    **Note:** however using plain JSON serializer/deserializer in the console will work just as fine.

'''
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers.json import Serializer as OverloadedSerializer
from django.core.serializers.json import Deserializer
#from wadofstuff.django.serializers.python import Serializer as OverloadedSerializer
from django.utils import simplejson
from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.gis.geos.geometry import GEOSGeometry
from django.utils import simplejson as json
from django.core.serializers.python import Deserializer as PythonDeserializer


class Serializer(OverloadedSerializer):
    def handle_field(self, obj, field):
        """
        If field is of GeometryField than encode otherwise call parent's method
        """
        value = field._get_val_from_obj(obj)
        if isinstance(field, GeometryField):
            self._current[field.name] = value
        else:
            super(Serializer, self).handle_field(obj, field)

    
    def end_serialization(self):
        simplejson.dump(self.objects, self.stream, cls=DjangoGEOJSONEncoder, **self.options)

class DjangoGEOJSONEncoder(DjangoJSONEncoder):
    """
    DjangoGEOJSONEncoder subclass that knows how to encode GEOSGeometry value
    """
    
    def default(self, o):
        """ overload the default method to process any GEOSGeometry objects otherwise call original method """ 
        if isinstance(o, GEOSGeometry):
            dictval = json.loads(o.geojson)
            #raise Exception(o.ewkt)
            dictval['__GEOSGeometry__'] = ['__init__', [o.ewkt]] #json class hint; see http://json-rpc.org/wiki/specification
            return dictval
        else:
            super(DjangoGEOJSONEncoder, self).default(o)

def Deserializer(stream_or_string, **options):
    """
    Deserialize a stream or string of JSON data.
    """
    def GEOJsonToEWKT(dict):
        """ 
        Convert to a string that GEOSGeometry class constructor can accept. 
        
        The default decoder would pass our geo dict object to the constructor which 
        would result in a TypeError; using the below hook we are forcing it into a 
        ewkt format. This is accomplished with a class hint as per JSON-RPC 
        """ 
        if '__GEOSGeometry__' in dict: # using class hint catch a GEOSGeometry definition 
            return dict['__GEOSGeometry__'][1][0]
        
        return dict
    if isinstance(stream_or_string, basestring):
        stream = StringIO(stream_or_string)
    else:
        stream = stream_or_string
    for obj in PythonDeserializer(simplejson.load(stream, object_hook=GEOJsonToEWKT), **options):
        yield obj
