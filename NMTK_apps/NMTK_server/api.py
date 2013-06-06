from NMTK_server.resources import ModelResource
from NMTK_server import models
from tastypie.authentication import SessionAuthentication
from tastypie import fields, utils
from django.contrib.auth.models import User
from tastypie.authorization import Authorization
from django.forms.models import model_to_dict


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
        elif bundle.obj.pj <> bundle.request.user.pk:
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
            return True
        
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
    class Meta:
        queryset=User.objects.filter(is_active=True)
        results_name='user'
        authentication=SessionAuthentication()
        authorization=UserResourceAuthorization()
        excludes=('password',)
        
    def obj_create(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_create``.
        """
        bundle.obj = self._meta.object_class()

        for key, value in kwargs.items():
            if key == 'password':
                bundle.obj.set_password('password')
            else:
                setattr(bundle.obj, key, value)

        self.authorized_create_detail(self.get_object_list(bundle.request), bundle)
        bundle = self.full_hydrate(bundle)
        return self.save(bundle)
    
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
                    
    def obj_update(self, bundle, skip_errors=False, **kwargs):
        """
        A ORM-specific implementation of ``obj_update``.
        """
        if not bundle.obj or not self.get_bundle_detail_data(bundle):
            try:
                lookup_kwargs = self.lookup_kwargs_with_identifiers(bundle, kwargs)
            except:
                # if there is trouble hydrating the data, fall back to just
                # using kwargs by itself (usually it only contains a "pk" key
                # and this will work fine.
                lookup_kwargs = kwargs

            try:
                bundle.obj = self.obj_get(bundle=bundle, **lookup_kwargs)
            except ObjectDoesNotExist:
                raise NotFound("A model instance matching the provided arguments could not be found.")
            
        if bundle.data.get('password'):
            bundle.obj.set_password(bundle.data['password'])
        # if the user is not a superuser, only the password can be changed.
        if not bundle.request.user.is_superuser:
            bundle.data=model_to_dict(bundle.obj)
        bundle = self.full_hydrate(bundle)
        
        return self.save(bundle, skip_errors=skip_errors)

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



class DataFileResource(ModelResource):
    user=fields.ToOneField(UserResource, 'user')
    class Meta:
        queryset = models.DataFile.objects.all()
        authorization=DataFileResourceAuthorization()
        resource_name = 'datafile'
        allowed_methods=['get','post','delete',]
        authentication=SessionAuthentication()

    def pre_save(self, bundle):
        bundle.obj.user=bundle.request.user
        return bundle

class ToolResource(ModelResource):
    class Meta:
        queryset = models.Tool.objects.filter(active=True)
        resource_name = 'tool'
        authentication=SessionAuthentication()
        fields=['name']
        
class ToolConfigResource(ModelResource):
    class Meta:
        queryset = models.ToolConfig.objects.all()
        resource_name = 'tool_config'
        authentication=SessionAuthentication()
        fields=['json_config']
        
class JobResource(ModelResource):
    class Meta:
        queryset = models.Job.objects.all()
        resource_name = 'job'
        authentication=SessionAuthentication()
        fields=['json_config']
        
class JobStatusResource(ModelResource):
    class Meta:
        queryset = models.JobStatus.objects.all()
        resource_name = 'job_status'
        authentication=SessionAuthentication()
        fields=['json_config']
        