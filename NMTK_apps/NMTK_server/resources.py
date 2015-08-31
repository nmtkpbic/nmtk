'''
Some NMTK specific optimizations/code changes for TastyPie
'''
from tastypie.resources import *
from tastypie.resources import Resource as TastyPieResource
from tastypie.resources import ModelResource as TastyPieModelResource
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)


class ModelResource(TastyPieModelResource):

    def pre_save(self, bundle):
        return bundle

    def deserialize(self, request, data, format=None):
        """
        Given a request, data and a format, deserializes the given data.

        It relies on the request properly sending a ``CONTENT_TYPE`` header,
        falling back to ``application/json`` if not provided.

        Mostly a hook, this uses the ``Serializer`` from ``Resource._meta``.
        """
        if format is None:
            format = request.META.get('CONTENT_TYPE', 'application/json')

        if format == 'application/x-www-form-urlencoded':
            '''
            Handle the case of a simple POST form
            '''
            logger.debug('Handling a simple POST request')
            deserialized = request.POST
        elif format.startswith('multipart'):
            if request.POST:
                logger.debug('Handling a multipart post with POST data')
                deserialized = request.POST.copy()
            else:
                deserialized = {}
            for name, value in request.FILES.iteritems():
                if (name == self._meta.resource_name):
                    logger.debug('File for %s, Content type: %s',
                                 name, value.content_type)
                    deserialized = self._meta.serializer.deserialize(
                        value.read(), value.content_type)
                    del request.FILES[name]
                    break
            for k, v in request.FILES.items():
                if isinstance(v, (list, tuple)) and len(v) == 1:
                    logger.debug('%s=%s (%s??!? unlisting!)', k, v, type(v))
                    request.FILES[k] = v[0]
                else:
                    logger.debug("%s=%s is ok", k, v)
            for k, v in request.FILES.iteritems():
                deserialized[k] = v
#            deserialized.update(request.FILES)
            for k, v in deserialized.items():
                logger.debug('DESERIALIZED: %s=%s (%s)', k, v, type(v))
        else:
            deserialized = self._meta.serializer.deserialize(data,
                                                             format=format)

        return deserialized

    def alter_list_data_to_serialize(self, request, data):
        data['meta']['refresh_interval'] = 60000
        return data

    def save(self, bundle, skip_errors=False):
        '''
        Copied directly from TastyPie's resources.ModelResource.save() method.
        Basically, this is where we insert (for NMTK) a pre_save method call
        that allows for fields like user ownership by (which are generally read only)
        to be updated before saving based on bundle data.
        '''
        bundle = self.pre_save(bundle)
        self.is_valid(bundle)

        if bundle.errors and not skip_errors:
            raise ImmediateHttpResponse(
                response=self.error_response(
                    bundle.request, bundle.errors))

        # Check if they're authorized.
        if bundle.obj.pk:
            self.authorized_update_detail(
                self.get_object_list(
                    bundle.request), bundle)
        else:
            self.authorized_create_detail(
                self.get_object_list(
                    bundle.request), bundle)

        # Save FKs just in case.
        self.save_related(bundle)

        # Save the main object.
        # the pre-save hook allows for modifications to the object prior to
        # saving it.

        bundle.obj.save()
        bundle.objects_saved.add(self.create_identifier(bundle.obj))

        # Now pick up the M2M bits.
        m2m_bundle = self.hydrate_m2m(bundle)
        self.save_m2m(m2m_bundle)
        return bundle
