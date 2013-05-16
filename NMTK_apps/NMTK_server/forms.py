from django import forms
from NMTK_server import models
from django.core.urlresolvers import reverse_lazy
import json
import logging
logger=logging.getLogger(__name__)

class JobSubmissionForm(forms.ModelForm):
    def __init__(self, *pargs,**kwargs):
        super(JobSubmissionForm, self).__init__(*pargs, **kwargs)
        self.fields["tool"].queryset=models.Tool.objects.filter(active=True)
    
    def clean(self):
        cleaned_data=super(JobSubmissionForm, self).clean()
        if cleaned_data.has_key('file'):
            try:
                json.loads(cleaned_data.get('file').read())
            except ValueError, e:
                self._errors["file"] = self.error_class(["JSON file Data is not valid: %s" % e])
                del cleaned_data['file']
        return cleaned_data
    
    class Meta:
        model=models.Job
        fields=('tool','file')
      
class ToolConfigForm(forms.Form):
    '''
    Construct a form object using the configuration for
    a particular tool.  This should allow the user to
    either provide "field mappings" from the source to the destination 
    file, or set configuration variables (parameters) (or both.)
    
    This form requires two input arguments:
        - config: the FULL config object for this particular
                  tool.
        - source_fields: A list of the FIELDS that were in the data source
                         this is likely to come from OGRInfo, and is basically
                         a mapping from the fields in the data file to those fields
                         that are required/exepected by the model for processing.
    '''
    mappings={'number': forms.DecimalField,
              'string': forms.CharField,
              'integer': forms.IntegerField,}
    def __init__(self, *args, **kwargs):
        if kwargs.has_key('job'):
            job=kwargs.pop('job')
        else:
            job=args[0]
            args=args[1:]
        super(ToolConfigForm, self).__init__(*args, **kwargs)
        config=job.tool.toolconfig.json_config
        data=json.loads(job.file.read())
        source_fields=data['features'][0]['properties'].keys()
#        logger.debug('Fields are %s', source_fields)
        # build choices so the user can choose the mapping(s)
        dataChoices=[(field, field) for field in source_fields]          
        input=config['input']
        self.fields['job_id']=forms.CharField(initial=job.pk,
                                              widget=forms.HiddenInput)
        for field_name, data in input['properties'].iteritems():
            # these are the values the user needs to provide.
            if data['type'] in self.mappings:
                fieldObj=self.mappings[data['type']]
                fargs={'required': data.get('required', False),
                       'help_text': data.get('description','')}
                if data.has_key('default'):
                    fargs['initial']=data['default']
                self.fields[field_name]=fieldObj(**fargs)
            # These are the fields that need to come from the data source.
            elif data['type'] == 'property':
                fargs={'choices': dataChoices,
                       'help_text': data.get('description','')}
                if field_name in source_fields:
                    fargs['initial']=field_name
                self.fields[field_name]=forms.ChoiceField(**fargs)
            
        