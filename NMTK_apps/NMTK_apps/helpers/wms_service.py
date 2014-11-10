from django.http import HttpResponse, HttpResponseBadRequest
import subprocess
from django.conf import settings

import djpaste
import logging
import os
import math
import colorsys
from NMTK_server import tasks
from PIL import Image, ImageDraw, ImageFont
from django.template.loader import render_to_string

logger=logging.getLogger(__name__)

# Given a min and max value, and a value (somewhere in the middle)
# return a suitable pseudo-color to match.
def hsvcolorramp(val, minval=0, maxval=255):
    if minval == maxval:
        h=180
    else:
        h=float(val-minval)/(maxval-minval)*120
    g,r,b=colorsys.hsv_to_rgb(h/360,1.0,1.0)
    return int(r*255),int(g*255),int(b*255)


def rgbcolorramp(val, minval=0, maxval=255,
                 start_color=(0,0,0), end_color=(255,255,255)):
    '''
    Function to generate a color ramp using RGB colors.  Here we use
    start/end values of colors and just interpolate integer values between
    for steps.  The default is equal parts r/g/b generating a grey-scale ramp.
    
    This is a RGB color ramp, which will work for lots of "generic" ramps, but
    is distinctly different than our HSV ramp (which is the epitome of pretty ;-) ) 
    '''
    # Compute the position among the range - bounded by the max and min value.
    position=max(minval, min(val, maxval))/abs(minval*1.0-maxval*1.0)
    color=[]
    for i in range(3):
        color.append(start_color[i]+int((end_color[i]-start_color[i])*position))
    return tuple(color)

def generateColorRampLegendGraphic(min_text, max_text, 
                                   height=16, width=258, border=1, units=None,
                                   ramp_function=lambda val, min, max: hsvcolorramp(val,min,max),
                                   other_features_color=None):
    '''
    Function to use a ramp function to generate a set of values for a color ramp.
    '''
    logger.debug('Units are %s', units)
    im=Image.new('RGB', (width, height), "black")
    draw=ImageDraw.Draw(im)
    start=border
    stop=height-border*2
    fixed=False
    if (max_text is not None and min_text is not None) and max_text==min_text:
        fixed=True
    for i in range(border, width-border*2):
        if not fixed:
            color="rgb({0},{1},{2})".format(*ramp_function(i, minval=0, 
                                                           maxval=width-(border*2)))
        else:
            color="rgb({0},{1},{2})".format(*ramp_function(0, 0, 0))
        draw.line((i, start, i, stop), fill=color)
    del draw
    
    font=ImageFont.truetype(settings.LEGEND_FONT,12)
    if max_text is not None and min_text is not None:
        # Generate the legend text under the image
        if not fixed:
            min_text_width, min_text_height = font.getsize('{0}'.format(min_text))
            max_text_width, max_text_height = font.getsize('{0}'.format(max_text))
            text_height=max(min_text_height, max_text_height)
            
            final_width=max(width, max_text_width, min_text_width)
        else:
            max_text_width, text_height=font.getsize('All Features')
            final_width=max(width, max_text_width)
        # The text height, plus the space between the image and text (1px)
        total_text_height=text_height+1
        logger.debug('Total text height is now %s', total_text_height)
        if units:
            units_width, units_height=font.getsize(units)
            final_width=max(final_width, units_width)
            # Another pixel for space, then the units text
            total_text_height = total_text_height + units_height + 1
            logger.debug('Total text height is now %s (post units)', 
                         total_text_height)
        im2=Image.new('RGB', (final_width, height+total_text_height+6), "white")
        im2.paste(im, (int((final_width-width)/2),0))
        text_pos=height+1
        draw=ImageDraw.Draw(im2)
        if not fixed:
            draw.text((1, text_pos),
                      '{0}'.format(min_text),
                      "black",
                      font=font)
            draw.text((final_width-(max_text_width+1), text_pos), 
                      '{0}'.format(max_text), 
                      "black", 
                      font=font)
            if units:
                text_pos = text_pos + text_height + 1
                placement=(int(final_width/2.0-((units_width+1)/2)), text_pos)
                draw.text(placement, 
                          units, 
                          "black", 
                          font=font)
        else:
            placement=(int(final_width/2.0-((max_text_width+1)/2)), text_pos)
            draw.text(placement, 
                      'All Features', 
                      "black", 
                      font=font)    
        del draw
    else:
        im2=im
        
        max_text_width, text_height=font.getsize('All Features')
        final_width=max(width, max_text_width)
        # The text height, plus the space between the image and text (1px)
        total_text_height=text_height+1
        logger.debug('Total text height is now %s', total_text_height)
        if units:
            units_width, units_height=font.getsize(units)
            final_width=max(final_width, units_width)
            # Another pixel for space, then the units text
            total_text_height = total_text_height + units_height + 1
            logger.debug('Total text height is now %s (post units)', 
                         total_text_height)
        im2=Image.new('RGB', (final_width, height+total_text_height+6), "white")
        im2.paste(im, (int((final_width-width)/2),0))
        text_pos=height+1
        draw=ImageDraw.Draw(im2)
        if not fixed:
            draw.text((1, text_pos),
                      '{0}'.format(min_text),
                      "black",
                      font=font)
            draw.text((final_width-(max_text_width+1), text_pos), 
                      '{0}'.format(max_text), 
                      "black", 
                      font=font)
            if units:
                text_pos = text_pos + text_height + 1
                placement=(int(final_width/2.0-((units_width+1)/2)), text_pos)
                draw.text(placement, 
                          units, 
                          "black", 
                          font=font)
        else:
            placement=(int(final_width/2.0-((max_text_width+1)/2)), text_pos)
            draw.text(placement, 
                      'All Features', 
                      "black", 
                      font=font)    
        del draw
        
    if other_features_color:
        im=im2
        
        
    
    return im2

def generateMapfile(datafile, max_value, min_value, style_field,
                    ramp_function, other_features_color):
    colors=[]
    if max_value and min_value:
        step=math.fabs((max_value-min_value)/256)
        v=low=min_value
        while v <= max_value+step:
            #logger.debug('Value is now %s', v)
            r,g,b=ramp_function(v, max_value, min_value)
            colors.append({'r': r,
                           'g': g,
                           'b': b,
                           'low': low ,
                           'high': v})
            low=v
            v += step or 1
    else:
        step=None
     
    dbtype='postgis'
    data={'datafile': datafile,
          'dbtype': dbtype,
          'result_field': style_field,
          'static': min_value == max_value,
          'min': min_value,
          'max': max_value,
          'colors': colors,
          'unmatched_color': other_features_color,
          'mapserver_template': settings.MAPSERVER_TEMPLATE }
    data['connectiontype']='POSTGIS'
    dbs=settings.DATABASES['default']
    data['connection']='''host={0} dbname={1} user={2} password={3} port={4}'''.format(dbs.get('HOST', None) or 'localhost',
                                                                                       dbs.get('NAME'),
                                                                                       dbs.get('USER'),
                                                                                       dbs.get('PASSWORD'),
                                                                                       dbs.get('PORT', None) or '5432')
    data['data']='nmtk_geometry from userdata_results_{0}'.format(datafile.id)
    data['highlight_data']='''nmtk_geometry from (select * from userdata_results_{0} where nmtk_id in (%ids%)) as subquery
                              using unique nmtk_id'''.format(datafile.id)
    
    # Determine which of the mapfile types to use (point, line, polygon...)
    for geom_type in ['point','line','polygon']:
        if geom_type in datafile.get_geom_type_display().lower():
            break

    res=render_to_string('NMTK_server/mapfile_{0}.map'.format(geom_type), 
                         data)
    return res

def handleWMSRequest(request, datafile):
    from NMTK_server import models
    style_field=request.GET.get('STYLE_FIELD', datafile.result_field or None)
    legend_units=request.GET.get('LEGEND_UNITS', None)
    ramp=request.GET.get('RAMP', None)
    attributes=datafile.field_attributes
    if style_field == datafile.result_field:
        legend_units=datafile.result_field_units
    if style_field and style_field not in attributes:
        logger.error('Field specified (%s) does not exist.', style_field)
        return HttpResponseBadRequest('Specified style field ({0}) does not exist'.format(style_field))
    if style_field:  
        field_attributes=attributes[style_field]
    else:
        field_attributes={}
    values_list=min_result=max_result=None
    if field_attributes.get('values',None):
        values_list=field_attributes['values']
    elif (field_attributes.has_key('type') and 
          field_attributes.get('type', None) not in ('text',)):
        min_result=field_attributes['min']
        max_result=field_attributes['max']
    else:
        # Here we have a text type without a range of values, so
        # we'll just style everything using a single color.
        values_list=[]
    # TODO: Handle date/time/datetime values in ramps properly and in the mapfile(s)
    ramp_function=lambda val, min, max: hsvcolorramp(val,min,max)
    ramp_id=0
    other_features=(102,153,102)
    if values_list is not None:
        try:
            if ramp:
                color_ramp_identifier=models.MapColorStyles.objects.get(pk=int(ramp))
                ramp_id=color_ramp_identifier.pk
                other_features=color_ramp_identifier.other_color
                ramp_function=lambda val, min, max: rgbcolorramp(val,min,max, 
                                                                 start_color=color_ramp_identifier.start_color,
                                                                 end_color=color_ramp_identifier.end_color)            
        except Exception, e:
            logger.exception('Invalid color ramp specified, or no valid color ramps exist.')
            return HttpResponseBadRequest('Invalid color ramp specified')

    # If there's a values_list then we'll let the WMS server generate the 
    # legend, since it would be using discrete colors anyway, and would be better
    # at creating the legend.
    if request.GET['REQUEST'].lower() == 'getlegendgraphic' and values_list is None:
        # Round the value to 4 significant digits.
        round_to_n = lambda x, n: round(x, -int(math.floor(math.log10(x))) + (n - 1))

        im=tasks.generateColorRampLegendGraphic(min_text=round_to_n(min_result,4),
                                                max_text=round_to_n(max_result,4),
                                                units=legend_units,
                                                ramp_function=ramp_function,
                                                other_features_color=other_features)
        response=HttpResponse(content_type='image/png')
        im.save(response, 'png')
        return response
    try:
        # Assume that the ramp won't change once it is made, so here we will 
        # just use the ramp id and datafile pk to specify a unique WMS
        # service, so we don't need to keep creating WMS services.
        if 'field_name' in field_attributes:
            mapfile_path=os.path.join(datafile.mapfile_path, 
                                      "wms_{0}_ramp_{1}_{2}.map".format(datafile.pk,
                                                                        ramp_id,
                                                                        field_attributes['field_name']) )
        else:
             mapfile_path=os.path.join(datafile.mapfile_path, 
                                       "wms_{0}.map".format(datafile.pk))
        if not os.path.exists(mapfile_path):
            mf=generateMapfile(datafile, max_result, min_result, 
                               style_field=style_field,
                               ramp_function=ramp_function,
                               other_features_color=other_features)
            with open(mapfile_path, 'w') as mapfile:
                mapfile.write(mf)
        # Create the app to call mapserver.
        app=djpaste.CGIApplication(global_conf=None, 
                                   script=settings.MAPSERV_PATH,
                                   include_os_environ=True,
                                   query_string=request.META['QUERY_STRING'],
                                   )
        environ=request.META.copy()
        environ['MS_MAPFILE']=str(mapfile_path)
        return app(request, environ)
    except djpaste.CGIError, e:
        logger.exception(e)
        return HttpResponseBadRequest()
    