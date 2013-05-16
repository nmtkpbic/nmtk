from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
   url('^(?P<tool_name>[^/]*)$', 'MN_model.views.toolBase', {}, name='tool_base'),
   url('^(?P<tool_name>[^/]*)/analyze$', 'MN_model.views.runModel', { }, 
       name='runModel'),
   url('^(?P<tool_name>[^/]*)/config$', 'MN_model.views.generateToolConfiguration', {},
       name='ToolConfiguration'),
   url('^(?P<tool_name>[^/]*)/docs', 'MN_model.views.generateDocs', {}, 
       name='MN_Documentation'),
)
