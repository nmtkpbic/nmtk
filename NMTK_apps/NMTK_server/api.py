from NMTK_server.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from NMTK_server import models
from django.conf.urls import patterns, include, url
from tastypie.exceptions import Unauthorized
from tastypie.authentication import SessionAuthentication
from tastypie import fields, utils
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from tastypie.authorization import Authorization
from django.forms.models import model_to_dict
from tastypie.utils import trailing_slash
from django.core.servers.basehttp import FileWrapper
from django.core.exceptions import ObjectDoesNotExist
from tastypie.resources import csrf_exempt
from django.http import HttpResponse, Http404
from NMTK_server import forms
import simplejson as json
from tastypie.validation import Validation
import logging
import re
import os
logger=logging.getLogger(__name__)

class UserResourceValidation(Validation):
    def is_valid(self, bundle, request=None):
        errors = {}
        if bundle.request.method == 'POST':
            if not bundle.data:
                return {'__all__': 'Invalid Data'}
    
    
            if bundle.data.has_key('username'):
                count=models.User.objects.filter(username=bundle.data['username']).count()
            if count > 0:
                errors['username']='Sorry, that username is not available'
        if bundle.request.method in ('PUT','PATCH'):
            if (bundle.data.has_key('password') and 
                not bundle.request.user.is_superuser):
                if not bundle.data.has_key('old_password'):
                    errors['__all__']='old_password must be supplied when changing password'
                elif not bundle.request.user.check_password(bundle.data['old_password']):
                    errors['__all__']='Old password supplied is invalid'                
        return errors

class UserResourceAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        '''
        This gets a queryset (object_list) and returns a new one.  The key
        here is that we are apply *additional* filters to the default 
        queryset to restrict the output back to the user.
        
        In this case, we check to see if the user is a site admin, if they are
        then they are able to see *all* the records for active users.
        
        If they are *not* a site admin, we restrict viewing of data to the
        username that matches the current logged in user.  In short, you 
        can see your information, but noone elses.
        '''
        if bundle.request.user.is_superuser:
            return object_list
        return object_list.filter(pk=bundle.request.user.pk)

    def read_detail(self, object_list, bundle):
        '''
        This should get a list (containing a single record).  It should
        either return an error indicating the record is not accessible by
        the user, or it should simply return.
        
        In this case, raising NotFound seems to be the only option that 
        causes the server to continue to function without an exception.  Other
        things (like not authorized) cause a 500
        '''
        if bundle.request.user.is_superuser:
            return True
        elif bundle.obj.pk <> bundle.request.user.pk:
            raise Unauthorized('You lack the privilege to access this resource')
        return True

    def create_list(self, object_list, bundle):
        '''
        This method should, when given a list of objects, return a new list
        of objects representing the objects that are to be created.  In the case
        of this model, only superusers can create new users, so we simply return
        the empty list when they try to add objects.
        '''
        if bundle.request.user.is_superuser:
            return object_list
        raise Unauthorized('You lack the privilege to create this resource')

    def create_detail(self, object_list, bundle):
        '''
        Each record being created is passed through this method, which is
        used to determine if the object can be created - an exception means
        that it cannot, a True (or anything else for that matter) means that it
        can be created.  In our case, we only allow this record to be created
        when the user is an admin user.
        '''
        if not bundle.request.user.is_superuser:
            raise Unauthorized('You lack the privilege to create this resource')
        return True

    def update_list(self, object_list, bundle):
        '''
        A list of objects to be updated.  In the case of a superuser, we let
        them do what they want.  In the case of any other user, they can only
        modify their user record - noone elses.  Elsewhere we will limit what 
        they can modify about this record - and limit them to only changing
        their password.
        '''
        # Superusers can do what they want.
        if bundle.request.user.is_superuser:
            return object_list
        raise Unauthorized('You lack the privilege to update resources this way')
    

    def update_detail(self, object_list, bundle):
        '''
        In this case, we simply force updates to the model to occur
        '''
        if bundle.request.user.is_superuser:
            return True
        elif bundle.obj.pk == bundle.request.user.pk:
            if bundle.data.has_key('password'):
                return True
            else:
                raise Unauthorized('You may only change your own password')
        
        raise Unauthorized('You lack the privilege to access this resource')

    def delete_list(self, object_list, bundle):
        # Sorry user, no deletes for you
        if bundle.request.user.is_superuser:
            return object_list
        raise Unauthorized("This resource does not allow deletes.")

    def delete_detail(self, object_list, bundle):
        if bundle.request.user.is_superuser:
            return True
        raise Unauthorized('You lack the privilege to access this resource')

class UserResource(ModelResource):
    date_joined=fields.DateTimeField('date_joined',readonly=True)
    last_login=fields.DateTimeField('last_login',readonly=True)
    class Meta:
        queryset=User.objects.filter(is_active=True)
        results_name='user'
        always_return_data = True
        authentication=SessionAuthentication()
        authorization=UserResourceAuthorization()
        validation=UserResourceValidation()
        excludes=('password','groups',)
        filtering= {'username': ALL,
                    'email': ALL}
        
    def pre_save(self,bundle):
        bundle=super(UserResource,self).pre_save(bundle)
        if bundle.data.has_key('password'):
            bundle.obj.set_password(bundle.data['password'])
        return bundle
    
    def obj_delete_list(self, bundle, **kwargs):
        """
        Translate a delete via the API to a "set inactive"
        """
        objects_to_delete = self.obj_get_list(bundle=bundle, **kwargs)
        deletable_objects = self.authorized_delete_list(objects_to_delete, bundle)

        for authed_obj in deletable_objects:
            authed_obj.is_active=False
            authed_obj.set_unusable_password()
            authed_obj.save()

    def obj_delete_list_for_update(self, bundle, **kwargs):
        """
        Translate a delete via the API to a "set inactive"
        """
        objects_to_delete = self.obj_get_list(bundle=bundle, **kwargs)
        deletable_objects = self.authorized_update_list(objects_to_delete, bundle)

        for authed_obj in deletable_objects:
            authed_obj.is_active=False
            authed_obj.set_unusable_password()
            authed_obj.save()
            
    def obj_delete(self, bundle, **kwargs):
        """
        Translate a delete via the API to a "set inactive"
        """
        if not hasattr(bundle.obj, 'delete'):
            try:
                bundle.obj = self.obj_get(bundle=bundle, **kwargs)
            except ObjectDoesNotExist:
                raise NotFound("A model instance matching the provided arguments could not be found.")

        self.authorized_delete_detail(self.get_object_list(bundle.request), bundle)
        bundle.obj.is_active=False
        bundle.obj.set_unusable_password()
        bundle.obj.save()

    def hydrate(self, bundle):
        if not bundle.request.user.is_superuser:
#             logger.debug(model_to_dict(bundle.obj))
            if bundle.obj.pk:
                data=model_to_dict(bundle.obj)
                del data['password']
                bundle.data.update(data)

        return super(UserResource, self).hydrate(bundle)

class DataFileResourceAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        '''
        This gets a queryset (object_list) and returns a new one.  The key
        here is that we are apply *additional* filters to the default 
        queryset to restrict the output back to the user.
        
        In this case, we check to see if the user is a site admin, if they are
        then they are able to see *all* the records for active users.
        
        If they are *not* a site admin, we restrict viewing of data to the
        username that matches the current logged in user.  In short, you 
        can see your information, but noone elses.
        '''
        return object_list.filter(user=bundle.request.user.pk)

    def read_detail(self, object_list, bundle):
        '''
        This should get a list (containing a single record).  It should
        either return an error indicating the record is not accessible by
        the user, or it should simply return.
        
        In this case, raising NotFound seems to be the only option that 
        causes the server to continue to function without an exception.  Other
        things (like not authorized) cause a 500
        '''
        if bundle.request.user.is_superuser:
            return True
        elif bundle.obj.user.pk <> bundle.request.user.pk:
            raise Unauthorized('You lack the privilege to access this resource')
        return True

    def create_list(self, object_list, bundle):
        '''
        This method should, when given a list of objects, return a new list
        of objects representing the objects that are to be created.  In the case
        of this model, only superusers can create new users, so we simply return
        the empty list when they try to add objects.
        '''
        logger.debug('Creating a new object')
        return object_list        

    def create_detail(self, object_list, bundle):
        '''
        Each record being created is passed through this method, which is
        used to determine if the object can be created - an exception means
        that it cannot, a True (or anything else for that matter) means that it
        can be created.  In our case, we only allow this record to be created
        when the user is an admin user.
        '''
        logger.debug('in create_detail')
        return True

    def update_list(self, object_list, bundle):
        '''
        A list of objects to be updated.  In the case of a superuser, we let
        them do what they want.  In the case of any other user, they can only
        modify their user record - noone elses.  Elsewhere we will limit what 
        they can modify about this record - and limit them to only changing
        their password.
        '''
        # Superusers can do what they want.
        if bundle.request.user.is_superuser:
            return object_list
        else:
            return [obj for obj in object_list 
                    if obj.user == bundle.request.user]    

    def update_detail(self, object_list, bundle):
        '''
        In this case, we simply force updates to the model to occur
        '''
        if bundle.request.user.is_superuser:
            return True
        elif bundle.obj.pk == bundle.request.user.pk:
            return True
        
        raise Unauthorized('You lack the privilege to access this resource')

    def delete_list(self, object_list, bundle):
        # Sorry user, no deletes for you
        if bundle.request.user.is_superuser:
            return object_list
        else:
            return [obj for obj in object_list 
                    if obj.user == bundle.request.user] 

    def delete_detail(self, object_list, bundle):
        if bundle.request.user.is_superuser:
            return True
        elif bundle.obj.user == bundle.request.user:
            return True
        raise Unauthorized('You lack the privilege to access this resource')

class DataFileResourceValidation(Validation):
    def is_valid(self, bundle, request=None):
        errors = {}
        if (not bundle.obj.pk and 
            not bundle.request.FILES.has_key('file')):
            errors['file']='A file must be provided when creating this resource'
        if (bundle.data.get('srid', False) and
            bundle.obj.status not in 
            (bundle.obj.IMPORT_FAILED,bundle.obj.PENDING)):
            errors['srid']='SRID can only be provided initially, ' + \
                           'or after a failed import'
        return errors

class DataFileResource(ModelResource):
    id=fields.IntegerField('id', readonly=True)
    status_message=fields.CharField('status_message', readonly=True,
                                    null=True)
    feature_count=fields.IntegerField('feature_count', readonly=True,
                                      null=True)
    content_type=fields.CharField('content_type', readonly=True,
                                  null=True)
    date_created=fields.DateTimeField('date_created', readonly=True,
                                      null=True)
    extent=fields.CharField('extent', readonly=True, null=True)
    srs=fields.CharField('srs', readonly=True, null=True)
    status=fields.CharField('status', readonly=True, null=True)
    geom_type=fields.CharField('geom_type', readonly=True, null=True)
    file=fields.CharField('file', readonly=True, null=True)
    geojson=fields.CharField('geojson_file', readonly=True, null=True)


    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/download%s$" % (self._meta.resource_name, 
                                                                           trailing_slash()), 
                                                                           self.wrap_view('download_detail_file'), 
                name="api_%s_download_detail" % (self._meta.resource_name,)),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/geojson%s$" % (self._meta.resource_name, 
                                                                           trailing_slash()), 
                                                                           self.wrap_view('download_detail_geojson'), 
                name="api_%s_download_detail_geojson" % (self._meta.resource_name,)),
            ]
        
    def download_detail_geojson(self, request, **kwargs):
        """
        Send a file through TastyPie without loading the whole file into
        memory at once. The FileWrapper will turn the file object into an
        iterator for chunks of 8KB.

        No need to build a bundle here only to return a file, lets look into the DB directly
        """
        try:
            if request.user.is_superuser:
                rec = self._meta.queryset.get(pk=kwargs['pk'])
            else:
                rec = self._meta.queryset.get(pk=kwargs['pk'],
                                              user=request.user)
        except ObjectDoesNotExist:
            raise Http404
        if not rec.processed_file:
            raise Http404
        
        
        wrapper = FileWrapper(open(rec.processed_file.path,'rb'))
        response = HttpResponse(wrapper, content_type='application/json') #or whatever type you want there
        response['Content-Length'] = rec.processed_file.size
        response['Content-Disposition'] = ('attachment; ' +
                                           'filename="data.geojson"')
        return response        

    def download_detail_file(self, request, **kwargs):
        """
        Send a file through TastyPie without loading the whole file into
        memory at once. The FileWrapper will turn the file object into an
        iterator for chunks of 8KB.

        No need to build a bundle here only to return a file, lets look into the DB directly
        """
        try:
            if request.user.is_superuser:
                rec = self._meta.queryset.get(pk=kwargs['pk'])
            else:
                rec = self._meta.queryset.get(pk=kwargs['pk'],
                                              user=request.user)
        except ObjectDoesNotExist:
            raise Http404
        if not rec.file:
            # if there are results, then they can download them
            raise Http404
            
        
        wrapper = FileWrapper(open(rec.file.path,'rb'))
        response = HttpResponse(wrapper, content_type=rec.content_type) #or whatever type you want there
        response['Content-Length'] = rec.file.size
        response['Content-Disposition'] = ('attachment; filename="%s"' % 
                                           (os.path.basename(rec.file.name)))
        return response        

    class Meta:
        queryset = models.DataFile.objects.all()
        authorization=DataFileResourceAuthorization()
        always_return_data = True
        resource_name = 'datafile'
        allowed_methods=['get','post','delete',]
        excludes=['file','processed_file','status', 'geom_type', 'fields']
        authentication=SessionAuthentication()
        validation=DataFileResourceValidation()
        filtering= {'status': ALL,
                    'user': ALL}

    def pre_save(self, bundle):
        '''
        Ensure that we properly store the user information when the object
        is created, and allow for the optional SRID parameter, but only when
        the import is PENDING (new) or has failed in the past.
        '''
        bundle.obj.user=bundle.request.user
        if bundle.request.FILES.has_key('file'):
            bundle.obj.file=bundle.request.FILES['file']
            if not bundle.obj.content_type:
                bundle.obj.content_type=bundle.request.FILES['file'].content_type
        if bundle.data.get('srid', False):
            logging.debug('SRID provided for import, storing')
            bundle.obj.srid=bundle.data['srid']
            bundle.obj.status=bundle.obj.PENDING
        if not bundle.obj.name:
            bundle.obj.name=os.path.basename(bundle.obj.file.name)
            
        return bundle
    
    def alter_list_data_to_serialize(self, request, data):
        '''
        Loop over the list of objects and count how many are currently pending,
        this is then used to update the importing count for the UI, so it knows
        how often to update itself (in milliseconds.)
        '''
        count=0
        for item in data['objects']:
            if item.obj.status in (item.obj.PENDING, item.obj.PROCESSING):
                count += 1
        if count:
            data['meta']['refresh_interval']=3000
        else:
            data['meta']['refresh_interval']=60000
        return data
    
    def dehydrate(self,bundle):
        '''
        Provide data for some fields that we return back to the user, making 
        things a bit more usable than the default TastyPie implementation allows.
        Note: These are all read-only fields, so we don't need to worry about  
        them during the hydrate cycle...
        '''
        if bundle.obj.file:
            bundle.data['file']=reverse("api_%s_download_detail" % 
                                        (self._meta.resource_name,),
                                        kwargs={'resource_name': self._meta.resource_name,
                                                'pk': bundle.obj.pk,
                                                'api_name': 'v1'})
        if bundle.obj.processed_file:
            bundle.data['geojson']="%sgeojson/" % (bundle.data['resource_uri'],)
        bundle.data['status']=bundle.obj.get_status_display()
        bundle.data['geom_type']=bundle.obj.get_geom_type_display()
        bundle.data['user'] = bundle.obj.user.username
        return bundle

class ToolResource(ModelResource):
    last_modified=fields.DateTimeField('last_modified', readonly=True,
                                       null=True)
    tool_server=fields.CharField('tool_server',readonly=True,
                                 null=True)
    config=fields.CharField(readonly=True, null=True,
                            help_text='Tool Configuration (as JSON)')
    class Meta:
        queryset = models.Tool.objects.filter(active=True)
        resource_name = 'tool'
        authentication=SessionAuthentication()
        always_return_data = True
        fields=['name', 'last_modified']
        allowed_methods=['get',]
        
    def dehydrate(self, bundle):
        bundle.data['config']=bundle.obj.toolconfig.json_config
        return bundle

        
#class ToolConfigResource(ModelResource):
#    class Meta:
#        queryset = models.ToolConfig.objects.all()
#        resource_name = 'tool_config'
#        authentication=SessionAuthentication()
#        fields=['json_config']
#        allowed_methods=['get',]

class JobResourceAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        '''
        This gets a queryset (object_list) and returns a new one.  The key
        here is that we are apply *additional* filters to the default 
        queryset to restrict the output back to the user.
        
        In this case, we check to see if the user is a site admin, if they are
        then they are able to see *all* the records for active users.
        
        If they are *not* a site admin, we restrict viewing of data to the
        username that matches the current logged in user.  In short, you 
        can see your information, but noone elses.
        '''
        if bundle.request.user.is_superuser:
            return object_list
        return object_list.filter(user=bundle.request.user.pk)

    def read_detail(self, object_list, bundle):
        '''
        This should get a list (containing a single record).  It should
        either return an error indicating the record is not accessible by
        the user, or it should simply return.
        
        In this case, raising NotFound seems to be the only option that 
        causes the server to continue to function without an exception.  Other
        things (like not authorized) cause a 500
        '''
        if bundle.request.user.is_superuser:
            return True
        elif bundle.obj.user.pk <> bundle.request.user.pk:
            raise Unauthorized('You lack the privilege to access this resource')
        return True
    
    def create_list(self, object_list, bundle):
        '''
        This method should, when given a list of objects, return a new list
        of objects representing the objects that are to be created.  In the case
        of this model, only superusers can create new users, so we simply return
        the empty list when they try to add objects.
        '''
        return object_list        

    def create_detail(self, object_list, bundle):
        '''
        Each record being created is passed through this method, which is
        used to determine if the object can be created - an exception means
        that it cannot, a True (or anything else for that matter) means that it
        can be created.  In our case, we only allow this record to be created
        when the user is an admin user.
        '''
        return True

    def update_list(self, object_list, bundle):
        '''
        A list of objects to be updated.  In the case of a superuser, we let
        them do what they want.  In the case of any other user, they can only
        modify their user record - noone elses.  Elsewhere we will limit what 
        they can modify about this record - and limit them to only changing
        their password.
        '''
        # Superusers can do what they want.
        if bundle.request.user.is_superuser:
            return object_list
        else:
            return [obj for obj in object_list 
                    if obj.user == bundle.request.user]    

    def update_detail(self, object_list, bundle):
        '''
        In this case, we simply force updates to the model to occur
        '''
        if bundle.request.user.is_superuser:
            return True
        elif bundle.obj.user == bundle.request.user:
            return True
        
        raise Unauthorized('You lack the privilege to access this resource')

    def delete_list(self, object_list, bundle):
        # Sorry user, no deletes for you
        if bundle.request.user.is_superuser:
            return object_list
        else:
            return [obj for obj in object_list 
                    if obj.user == bundle.request.user] 

    def delete_detail(self, object_list, bundle):
        if bundle.request.user.is_superuser:
            return True
        elif bundle.obj.user == bundle.request.user:
            return True
        raise Unauthorized('You lack the privilege to access this resource')
        
class JobResourceValidation(Validation):
    def is_valid(self, bundle, request=None):
        '''
        Once we have a job there are a few rules, you cannot change the
        tool or the file once the job is created, since doing so would
        end up possibly invalidating the configuration.  You cannot change the
        status, since it advances on it's own, and changing things once the 
        status has moved to active (for example) wouldn't make sense, so once it
        is active, we'll prevent changes.
        the validation will update the status to active once you send over
        a configuration that seems valid.  Then it's up to the tool to do the
        rest of the work in terms of processing/generating errors.
        '''
        kwargs={}
        kwargs['job']=bundle.obj
        errors={}
        # Special case with POST is that the data comes in as a unicode string.
        # convert it to the proper PYthon object.
        if isinstance(bundle.data.get('config'), (str, unicode)):
            bundle.data['config']=json.loads(bundle.data['config'])
        if bundle.obj.pk:
            for field in ['data_file','tool']:
                if (getattr(bundle.obj, '_old_%s' % (field,)) != 
                    getattr(bundle.obj, field)):
                    errors[field]=('This field cannot be changed, ' +
                                   'please create a new job instead')
        if bundle.obj.status != 'U':
            errors['status']= ('Cannot update a job once it has been ' +
                               'configured, please create a new job instead')  
        elif bundle.data.get('config', None):
            bundle.data['config']['job_id']=bundle.obj.pk
            if bundle.obj.config:
                kwargs['initial']=bundle.obj.config
            form=forms.ToolConfigForm(bundle.data.get('config'), 
                                      **kwargs)
            if form.is_valid():
                bundle.obj.config=form.cleaned_data
                bundle.obj.status=bundle.obj.ACTIVE
                return errors
            errors['config']=form.errors
            return errors
        return errors
         

class JobResource(ModelResource):
    job_id=fields.CharField('job_id', readonly=True)
    tool=fields.ToOneField(ToolResource, 'tool')
    data_file=fields.ToOneField(DataFileResource,'data_file',
                                null=False)
    form=fields.CharField(readonly=True,
                          help_text=('JavaScript Representation of form' + 
                                     ' (pass genform=1 as a GET parameter' +
                                     ' to generate)'))
    status=fields.CharField('status', readonly=True, null=True)
    tool_name=fields.CharField('tool_name', readonly=True, null=True)
    config=fields.CharField('config', readonly=True, null=True)
    results=fields.CharField('results',readonly=True, null=True,
                             help_text='URL to download results')
    class Meta:
        queryset = models.Job.objects.all()
        authorization=JobResourceAuthorization()
        validation=JobResourceValidation()
        always_return_data = True
        resource_name = 'job'
        authentication=SessionAuthentication()
        allowed_methods=['get','put','post','delete']
        filtering= {'status': ALL,
                    'user': ALL}

    def pre_save(self, bundle):
        bundle.obj.user=bundle.request.user
        return bundle
    
    def dehydrate(self, bundle):
        if bundle.obj.data_file:
            kwargs={}
            if bundle.obj.config:
                kwargs={'initial': bundle.obj.config }
            bundle.data['form']=forms.ToolConfigForm(job=bundle.obj, 
                                                     **kwargs).as_json()
        bundle.data['user'] = bundle.obj.user.username
        bundle.data['tool_name']=bundle.obj.tool.name
        bundle.data['status']=bundle.obj.get_status_display()
        if bundle.obj.status == bundle.obj.COMPLETE:
            bundle.data['results']="%sresults/" % (bundle.data['resource_uri'],)
            # This should work, but doesn't ?!?
#            bundle.data['results']=reverse('api_%s_download_detail' % (self._meta.resource_name,),
#                                           kwargs={'resource_name': self._meta.resource_name,
#                                                   'pk': str(bundle.obj.pk) })
        return bundle
    
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/results%s$" % (self._meta.resource_name, 
                                                                           trailing_slash()), 
                                                                           self.wrap_view('download_detail'), 
                name="api_%s_download_detail" % (self._meta.resource_name,)),
            ]

    def download_detail(self, request, **kwargs):
        """
        Send a file through TastyPie without loading the whole file into
        memory at once. The FileWrapper will turn the file object into an
        iterator for chunks of 8KB.

        No need to build a bundle here only to return a file, lets look into the DB directly
        """
        allow_download=False
        logger.debug('In download_detail with %s', kwargs)
        try:
            if request.user.is_superuser:
                rec = self._meta.queryset.get(pk=kwargs['pk'])
            else:
                rec = self._meta.queryset.get(pk=kwargs['pk'],
                                              user=request.user)
        except ObjectDoesNotExist:
            raise Http404
        if rec.results:
            # if there are results, then they can download them
            allow_download=True
            
        if allow_download:
            wrapper = FileWrapper(open(rec.results.path,'rb'))
            response = HttpResponse(wrapper, content_type='application/json') #or whatever type you want there
            response['Content-Length'] = rec.results.size
            response['Content-Disposition'] = 'attachment; ' + \
                                              'filename="result.geojson"'
            return response        
        else:
            raise Unauthorized('You lack the privileges required to download this file')

class JobStatusResourceAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        '''
        This gets a queryset (object_list) and returns a new one.  The key
        here is that we are apply *additional* filters to the default 
        queryset to restrict the output back to the user.
        
        In this case, we check to see if the user is a site admin, if they are
        then they are able to see *all* the records for active users.
        
        If they are *not* a site admin, we restrict viewing of data to the
        username that matches the current logged in user.  In short, you 
        can see your information, but noone elses.
        '''
        if bundle.request.user.is_superuser:
            return object_list
        return object_list.filter(job__user=bundle.request.user.pk)

    def read_detail(self, object_list, bundle):
        '''
        This should get a list (containing a single record).  It should
        either return an error indicating the record is not accessible by
        the user, or it should simply return.
        
        In this case, raising NotFound seems to be the only option that 
        causes the server to continue to function without an exception.  Other
        things (like not authorized) cause a 500
        '''
        if bundle.request.user.is_superuser:
            return True
        elif bundle.obj.user.pk <> bundle.request.user.pk:
            raise Unauthorized('You lack the privilege to access this resource')
        return True

class JobStatusResource(ModelResource):
    job=fields.ToOneField(JobResource, 'job')

    class Meta:
        queryset = models.JobStatus.objects.all()
        always_return_data = True
        authorization=JobStatusResourceAuthorization()
        resource_name = 'job_status'
        authentication=SessionAuthentication()
        allowed_methods=['get',]
        filtering= {'job': ALL,
                    'job_id': ALL}