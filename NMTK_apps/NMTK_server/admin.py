from django.contrib import admin
import models
from django.utils.safestring import mark_safe
from django.utils import simplejson as json
from django.conf import settings


#class ToolConfigAdmin(admin.TabularInline):
#    model=models.ToolConfig
#    extra=0
#    max_num=1
#    
#    readonly_fields=['json_config_pretty',]
#    fields=('json_config_pretty',)

class ToolServerAdmin(admin.ModelAdmin):
    pass

class ToolAdmin(admin.ModelAdmin):
    def json_configuration(self, obj):
        '''
        Return the web-safe json config...
        '''
        return ("""%s"""  
                         % (json.dumps(obj.toolconfig.json_config,
                                       sort_keys=True,
                                       separators=(',', ': ')
                                       ),))

    readonly_fields=('tool_path', 'tool_server', 'name','json_configuration',)
    class Media:
        js = ("NMTK_server/js/jquery-1.10.1.min.js" ,
              "NMTK_server/admin/js/tree.jquery.js" ,
              "NMTK_server/admin/js/treeview.js" ,)
        css = { "tree" : ("NMTK_server/admin/css/jqtree.css",)
               }
    
    
class JobAdmin(admin.ModelAdmin):
    def download_results_link(self, obj):
        if obj.status==obj.COMPLETE:
            return mark_safe('''<a href="%s">Results</a>''' % 
                             (obj.results_link,))
        else:
            return 'Not Available'
        
    list_filter=['status','user']
    list_display=['tool','date_created','status','user', 'download_results_link']
    fields=['tool','date_created','status','download_results_link','config']
    readonly_fields=('tool','status','config','download_results_link','date_created',)

class JobStatusAdmin(admin.ModelAdmin):
    list_display=['job', 'timestamp', 'message']
    

class DataFileAdmin(admin.ModelAdmin):
    def data_file(self, obj):
        '''
        Used by the admin to provide a nice download URL.
        '''
        return mark_safe('''<a href="%s">%s</a>''' % (obj.url,
                                                      obj.name))
        
    def data_file_geojson(self, obj):
        return mark_safe('''<a href="%s">%s</a>''' % (obj.geojson_url,
                                                      obj.geojson_name))
    list_display=['id','user','data_file','date_created',
                  'feature_count','status']
    list_filter=['user']
    fields=['user','date_created','data_file','data_file_geojson',
            'content_type',
            'name',
            'status','status_message','srid','srs','feature_count',
            'extent','geom_type',
            'description']
    readonly_fields=fields[1:-1]
    


admin.site.register(models.ToolServer, ToolServerAdmin)
admin.site.register(models.Tool, ToolAdmin)
admin.site.register(models.Job, JobAdmin)
admin.site.register(models.JobStatus, JobStatusAdmin)
admin.site.register(models.DataFile, DataFileAdmin)
