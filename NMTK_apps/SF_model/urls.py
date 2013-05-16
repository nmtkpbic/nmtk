from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
   url('^(?P<tool_name>[^/]*)$', 'SF_model.views.toolBase', {}, name='tool_base'),
   url('^(?P<tool_name>[^/]*)/analyze$', 'SF_model.views.runModel', { }, 
       name='runModel'),
   url('^(?P<tool_name>[^/]*)/config$', 'SF_model.views.generateToolConfiguration', {},
       name='ToolConfiguration'),
   url('^(?P<tool_name>[^/]*)/docs', 'SF_model.views.generateDocs', {}, 
       name='SF_Documentation'),
)
