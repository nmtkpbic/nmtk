from NMTK_server.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from NMTK_server import models
from tastypie.exceptions import Unauthorized
from tastypie.authentication import SessionAuthentication
from tastypie import fields, utils
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from tastypie.authorization import Authorization
from django.forms.models import model_to_dict
from NMTK_server import forms
from tastypie.validation import Validation
import logging
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
    geojson_file=fields.CharField('geojson_file', readonly=True, null=True)
    class Meta:
        queryset = models.DataFile.objects.all()
        authorization=DataFileResourceAuthorization()
        resource_name = 'datafile'
        allowed_methods=['get','post','delete',]
        excludes=['file','processed_file','status', 'geom_type']
        authentication=SessionAuthentication()
        validation=DataFileResourceValidation()

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
            
        return bundle
    
    def dehydrate(self,bundle):
        '''
        Provide data for some fields that we return back to the user, making 
        things a bit more usable than the default TastyPie implementation allows.
        Note: These are all read-only fields, so we don't need to worry about  
        them during the hydrate cycle...
        '''
        if bundle.obj.file:
            bundle.data['file']=bundle.request.build_absolute_uri(bundle.obj.url)
        if bundle.obj.processed_file:
            bundle.data['geojson_file']=bundle.request.build_absolute_uri(bundle.obj.geojson_url)
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
        
class JobResource(ModelResource):
    tool=fields.ToOneField(ToolResource, 'tool')
    data_file=fields.ToOneField(DataFileResource,'data_file',
                                null=False)
    class Meta:
        queryset = models.Job.objects.all()
        authorization=JobResourceAuthorization()
        resource_name = 'job'
        authentication=SessionAuthentication()
        allowed_methods=['get','put','post','delete']

    def pre_save(self, bundle):
        bundle.obj.user=bundle.request.user
        return bundle
    
    def dehydrate(self,bundle):
        if bundle.obj.data_file:
            kwargs={}
            if bundle.obj.config:
                kwargs={'initial': bundle.obj.config }
            bundle.data['form']=forms.ToolConfigForm(bundle.obj, 
                                                     **kwargs).as_json()
        bundle.data['user'] = bundle.obj.user.username
        return bundle

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
    job=fields.ToOneField(JobResource, 'tool')

    class Meta:
        queryset = models.JobStatus.objects.all()
        authorization=JobStatusResourceAuthorization()
        resource_name = 'job_status'
        authentication=SessionAuthentication()
        allowed_methods=['get',]
        