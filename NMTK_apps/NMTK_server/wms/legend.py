from django.conf import settings

import logging
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from itertools import izip

# We really just use this to get the color ramps it has available - it 
# gives us RGB colors for a wide range of things.
import matplotlib.pyplot as plt

logger=logging.getLogger(__name__)


class LegendGenerator(object):
    '''
    An NMTK Server class used to generate and manage legend objects.
    '''
    
    def __init__(self, color_format, min_value=None, max_value=None, 
                 reverse=False, steps=255, values_list=None,
                 min_text=None, max_text=None, units=None,
                 other_features_color=None):
        '''
        There are really two ways this piece of code works - either by
        using a values list (discrete values) or a min/max value.  In the 
        latter case the assumption is that we're attempting to generate
        a color ramp of values (encompassing ranges).  In the former, the
        assumption is that we'll use discrete values split evenly across
        the specified color format/ramp
        '''
        self.units=units
        self.values_list=values_list
        self.steps=steps # The number of steps in the range.
        self.other_features_color=other_features_color

        # If the user provided min/max information then we'll need to generate
        # text under the final legend graphic showing ranges (and units), that's
        # where the code below comes in handy.  In the values list case
        # we'll generate a vertical legend, where range values are irrelevant.
        round_to_n = lambda x, n: round(x, -int(np.floor(np.log10(x))) + (n - 1))

        if not max_text and max_value:
            max_text='{0}'.format(round_to_n(max_value, 4))
        if not min_text and min_value:
            min_text='{0}'.format(round_to_n(min_value, 4))
        self.max_text=max_text
        self.min_text=min_text
        self.min_value=min_value
        self.max_value=max_value            
            
        # Verify that the user has chosen to use one of the available color
        # ramp formats.  If they reverse it, then append an _r so that the code
        # knows to use the reverse of the ramp as appropriate.
        if color_format not in [v2 for v in self.supported_formats() for v2 in v[1]]:
            raise Exception('Unsupported color format specified')
        if reverse:
            color_format='{0}_r'.format(color_format)
        self.cmap=plt.get_cmap(color_format)
        
    def __iter__(self):
        '''
        Iterate over the values that are contained in each step (dependent on
        the steps provided to the constructor, as well as the max/min color
        provided.)  The idea here is that one could iterate over
        each of the available steps.
        
        The value iterator returns a step number, and a value indicating the 
        minimum value (greater than or equal to) that this step should match.
        
        For a min/max range it should be noted that the final color (highest one) 
        will be uniquely styled with the highest/last color value.  
        '''
        
        if self.min_value is not None and self.max_value is not None and self.min_value != self.max_value:
            # This is tricky, since we need to ensure that the last max value
            # we get is included in the list of values - otherwise
            # we end up not matching the last few features!
            self.value_iterator=enumerate(np.linspace(self.min_value, self.max_value, num=self.steps))
        elif self.values_list:
            # Returns an integer (step number) and corresponding value pair,
            # in this case the min/max values are the same since we are using a 
            # values list.  Generating the color uses only the step number...
            # Here we get a list of integer values..
            self.value_iterator=izip(map(int, 
                                         np.linspace(0, self.steps, num=max(3,len(self.values_list)))), 
                                     self.values_list)
        else:
            self.value_iterator=iter([])
        return self
        
    
    def unmatched(self):
        '''
        A generic color to return based on the current ramp for "all values"
        type displays.  This returns an dictionary containing the values..
        '''
        if self.other_features_color:
            colorset_nonbytes=colorset=self.other_features_color + (1,)
        else:
            colorset=self.cmap(step, bytes=True)
            colorset_nonbytes=self.cmap(step, bytes=False)
        color={'rgba': colorset[:4],
               'rgb': colorset[:3],
               'type': 'other',
               'opacity': int(colorset_nonbytes[-1]*100)}
        return color
    
    
    def next(self):
        '''
        The "other" part of the iterator this should return a dictionary containing
        a color key (with an r,g,b tuple) and either a "value" (indicating a 
        single value) or a 'max' keys - indicating a range that 
        this color should be used for (less than match.)
        
        The opacity is a value between 0 and 1 indicating how opaque the color 
        should be (1 indicates fully opaque/100% opaque)
        '''
        # We use the value iterator to get the step and the min/max
        # values for the color.
        step, value=self.value_iterator.next()
        logger.debug('Next iterated value is %s, %s', step, value)   
        try:
            colorset=self.cmap(step, bytes=True)
            colorset_nonbytes=self.cmap(step, bytes=False)
            color={'rgba': colorset[:4],
                   'rgb': colorset[:3],
                   'opacity': int(colorset_nonbytes[-1]*100)}
            if self.values_list:
                key='value'
                color['type']='values'
            else:
                key='max'
                color['type']='ramp'
            color[key]=value
        except Exception, e:
            logger.exception('Failed to get value: %s, %s, %s',
                             values, self.values_list, color)
            raise e
        return color
    
    @staticmethod
    def supported_formats():
        """
        Reference for colormaps included with Matplotlib.
        
        This reference example shows all colormaps included with Matplotlib. Note that
        any colormap listed here can be reversed by appending "_r" (e.g., "pink_r").
        These colormaps are divided into the following categories:
        
        Sequential:
            These colormaps are approximately monochromatic colormaps varying smoothly
            between two color tones---usually from low saturation (e.g. white) to high
            saturation (e.g. a bright blue). Sequential colormaps are ideal for
            representing most scientific data since they show a clear progression from
            low-to-high values.
        
        Diverging:
            These colormaps have a median value (usually light in color) and vary
            smoothly to two different color tones at high and low values. Diverging
            colormaps are ideal when your data has a median value that is significant
            (e.g.  0, such that positive and negative values are represented by
            different colors of the colormap).
        
        Qualitative:
            These colormaps vary rapidly in color. Qualitative colormaps are useful for
            choosing a set of discrete colors. For example::
        
                color_list = plt.cm.Set3(np.linspace(0, 1, 12))
        
            gives a list of RGB colors that are good for plotting a series of lines on
            a dark background.
        
        Miscellaneous:
            Colormaps that don't fit into the categories above.
        
        """
        return [('Sequential 1',     ['Blues', 'BuGn', 'BuPu',
                                    'GnBu', 'Greens', 'Greys', 'Oranges', 'OrRd',
                                    'PuBu', 'PuBuGn', 'PuRd', 'Purples', 'RdPu',]),
                ('Sequential 2',     ['Reds', 'YlGn', 'YlGnBu', 'YlOrBr', 'YlOrRd',
                                    'afmhot', 'autumn', 'bone', 'cool', 'copper',
                                    'gist_heat', 'gray', 'hot', 'pink',
                                    'spring', 'summer', 'winter']),
                ('Diverging',      ['BrBG', 'bwr', 'coolwarm', 'PiYG', 'PRGn', 'PuOr',
                                    'RdBu', 'RdGy', 'RdYlBu', 'RdYlGn', 'Spectral',
                                    'seismic']),
                ('Qualitative',    ['Accent', 'Dark2', 'Paired', 'Pastel1',
                                    'Pastel2', 'Set1', 'Set2', 'Set3']),
                ('Miscellaneous',  ['gist_earth', 'terrain', 'ocean', 'gist_stern',
                                    'brg', 'CMRmap', 'cubehelix',
                                    'gnuplot', 'gnuplot2', 'gist_ncar',
                                    'nipy_spectral', 'jet', 'rainbow',
                                    'gist_rainbow', 'hsv', 'flag', 'prism'])]
        
        
        
        
    def generateSampleRamp(self, height=16, width=257):
        im=Image.new('RGBA', (width, height), "black")
        draw=ImageDraw.Draw(im)
        start=border=1
        stop=height-border*2
        i=1
        for color in self:
            color="rgba({0},{1},{2},{3})".format(*color['rgba'])
            draw.line((i, start, i, stop), fill=color)
            i += 1
        del draw
        return im
        
    def generateFixedColorLegendGraphic(self, color_values, 
                                        units=None,
                                        height=16, width=258):
        '''
        Function to use a ramp function to generate a set of values for a legend
        graphic.  This is used when there's a limited list of colors for the legend.
        '''
        
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
    
    def generateColorRampLegendGraphic(self, min_text, max_text, 
                                       height=16, width=258, border=1, units=None,
                                       ramp_function=lambda val, min, max: hsvcolorramp(val,min,max),
                                       other_features_color=None):
        '''
        Function to use a ramp function to generate a set of values for a color ramp.
        '''
        im=Image.new('RGB', (width, height), "black")
        draw=ImageDraw.Draw(im)
        start=border
        stop=height-border*2
        for i in range(border, width-border*2):
            color="rgb({0},{1},{2})".format(*ramp_function(i, 0, width-(border*2)))
            draw.line((i, start, i, stop), fill=color)
        del draw
        
        font=ImageFont.truetype(settings.LEGEND_FONT,12)
        if max_text is None and min_text is None:
            im2=im
        else:
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
            del draw
        if other_features_color:
            '''
            Here we generate legend graphics for the color for "other" features.
            TODO
            '''
            im=im2
        return im2