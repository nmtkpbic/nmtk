'''
All the tool configs are stuck here, the name of the variable matches
the tool name,
tool_config=getattr(tool_configs, 'ols_ped')
'''
tools=['ped',]

ped={'info': {'name': 'Pedestrian Intersection Volume Model (San Francisco)',
                 'text': 'Application of the San Francisco Pedestrian Intersection Volume Model',
         'version': '0.1'},
         'sample': {},
         'documentation': {'links': {'Pedestrian Intersection Volume Model (San Francisco)': None}},
         'input': {'description': 'The indicated properties should be ' +   \
                                  'provided for each row of input data. ' + \
                                  ' Omitting a property will result in ' +  \
                                  'an incomplete execution of the model ' + \
                                  'as the missing property and its ' +      \
                                  'coefficients will be omitted from the' + \
                                  ' model entirely.',
                   'properties': {'constant': {'description': 'Constant value',
                                               'type': 'number',
                                               'default': 12.9,
                                               'required': True},
                                  # Coefficients
                                  'quarter_mile_households_coeff': {'description': 'Coefficient for Total households within 1/4 mile (10,000s)',
                                                  'type': 'number',
                                                  'default': 1.81,
                                                  'required': True, },
                                  'quarter_mile_employment_coeff': {'description': 'Coefficient for Total employment within 1/4 mile (100,000s)',
                                                'type': 'number',
                                                'default': 2.43,
                                                'required': True,},
                                  'high_activity_zone_coeff': {'description': 'Coefficient for Intersection is in a high-activity zone',
                                                  'type': 'number',
                                                  'default': 1.27,
                                                  'required': True,},
                                  'max_slope_coeff': {'description': 'Coefficient for Maximum slope on any intersection approach leg (100s)',
                                                  'type': 'number',
                                                  'default': -9.40,
                                                  'required': True,},
                                  'quarter_mile_campus_coeff': {'description': 'Coefficient for Intersection is within 1/4 mile of a university campus',
                                                  'type': 'number',
                                                  'default': .635,
                                                  'required': True,},
                                  'traffic_signal_coeff': {'description': 'Coefficient for Intersection is controlled by a traffic signal',
                                                  'type': 'number',
                                                  'default': 1.16,
                                                  'required': True,},
                                  
                                  'quarter_mile_households': {'description': 'Coefficient for Total households within 1/4 mile (10,000s)',
                                                  'type': 'property',
                                                  'required': True, },
                                  'quarter_mile_employment': {'description': 'Coefficient for Total employment within 1/4 mile (100,000s)',
                                                'type': 'property',
                                                'required': True,},
                                  'high_activity_zone': {'description': 'Coefficient for Intersection is in a high-activity zone',
                                                  'type': 'property',
                                                  'required': True,},
                                  'max_slope': {'description': 'Coefficient for Maximum slope on any intersection approach leg (100s)',
                                                  'type': 'property',
                                                  'required': True,},
                                  'quarter_mile_campus': {'description': 'Coefficient for Intersection is within 1/4 mile of a university campus',
                                                  'type': 'property',
                                                  'required': True,},
                                  'traffic_signal': {'description': 'Coefficient for Intersection is controlled by a traffic signal',
                                                  'type': 'property',
                                                  'required': True,},
                                 }}
        }

