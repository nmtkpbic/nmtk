from django.core.exceptions import ObjectDoesNotExist
from NMTK_apps.helpers import data_import
import datetime
from django.template.defaultfilters import floatformat
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.contrib.gis.gdal import OGRGeomType
from django.contrib.gis.gdal.error import SRSException, OGRException
from osgeo import ogr
from collections import namedtuple
import logging
import os
import traceback
logger=logging.getLogger(__name__)

def import_datafile(filename, model_name):
    try:
        uncompressor=data_import.UnCompressor(filename)
        filenames=uncompressor.uncompress()
        for fname in filenames:
            f=ogr.Open(fname)
            if f:
                df.driver=f.GetDriver().GetName()
                logger.debug("Driver is %s", f.GetDriver().GetName())
                # Don't import the file if it's a format we don't want to support.
                # of course, the write-only drivers are always excluded by default.
                if df.driver and df.driver not in data_import.EXCLUDED_FORMATS:
                    filename=fname
                    break
#                if os.path.splitext(fname)[1].lower() in data_import.SUPPORTED_EXTENSIONS:
#                    filename=fname
#                    break
    except Exception, e:
        logger.error('Failed to uncompress file(s): %s', e)
        df.status=('Failed to uncompress file(s): %s' % str(e))[:256]
        df.save()
        return False
    if not filename or not df.driver:
        df.status='Failed to recognize file format'
        df.save()
        logger.error('Unrecognized file types %s' % ','.join(filenames))
        return False
    logger.debug("Layer Count is %s", f.GetLayerCount())
    if f.GetLayerCount() > 1:
        message=('The file %s has %s layers (only single layer files are supported)' % (filename, f.GetLayerCount()))[:256]
        df.status=message
        df.save()
        logger.error(message)
        return False
    try:
        kwargs={}
        if df.srid:
            kwargs['srid']=df.srid
        loader=data_import.DataLoader(filename, **kwargs)
            
        #
        # Grab the BBOX for this geometry by inspecting the data file, then
        # generate a geometry object using that bbox
        #
        Extent=namedtuple('Extent',['x_min','x_max','y_min','y_max'])
        extent=Extent(*loader.geom_extent)
        
        # Construct the WKT...
        wkt='POLYGON((%(x_min)f %(y_min)f, %(x_min)f %(y_max)f, %(x_max)f %(y_max)f,  %(x_max)f %(y_min)f,  %(x_min)f %(y_min)f))'
        poly=GEOSGeometry(wkt % {'x_min': extent.x_min,
                                 'x_max': extent.x_max,
                                 'y_min': extent.y_min,
                                 'y_max': extent.y_max})
       
        #poly=Polygon.from_bbox((x_min,y_min,x_max,y_max))
        if not loader.geom_srid:
            df.status=("Unable to determine the projection for this data file (we don't know about it, or it's invalid!).  Perhaps you can specify the SRID?")[:256]
            df.save()
            return False
        poly.set_srid(int(loader.geom_srid))
        logger.debug('SRID is %s', loader.geom_srid)
        logger.debug('BBOX is %s', poly.ewkt)
        loader.import_datafile(model_name=model_name)
        
        if loader.success:
            pass
        else: # This should really never happen...
            raise Exception('Failed to import.')
    except Exception,e:
        logger.error(traceback.format_exc()) # Print the traceback.
        return False
    return True