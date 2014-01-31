from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
   url('^(?P<tool_name>[^/]*)$', 'test_tool.views.toolBase', {}, name='tool_base'),
   url('^(?P<tool_name>[^/]*)/analyze$', 'test_tool.views.runModel', { }, 
       name='runModel'),
   url('^(?P<tool_name>[^/]*)/config$', 'test_tool.views.generateToolConfiguration', {},
       name='ToolConfiguration'),
   url('^(?P<tool_name>[^/]*)/docs', 'test_tool.views.generateDocs', {}, 
       name='MN_Documentation'),
)
