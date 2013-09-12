'''
All the tool configs are stuck here, the name of the variable matches
the tool name,
tool_config=getattr(tool_configs, 'ols_ped')
'''
import os
import simplejson as json
tools=['ped',]
config_path=os.path.join(os.path.dirname(__file__), 'configs')

configs=dict((tool_name, json.load(open(os.path.join(config_path,'{0}.json'.format(tool_name)))))
              for tool_name in tools)
