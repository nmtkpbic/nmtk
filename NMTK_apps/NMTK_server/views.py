# Create your views here.
from django.shortcuts import render
from NMTK_server import forms
from NMTK_server import models
from NMTK_server.decorators import authentication
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.sites.models import get_current_site
import requests
import json
import os.path
import logging
import collections
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
import tempfile
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings
import dateutil.parser
import hashlib
import random
from registration import models as registration_models

logger = logging.getLogger(__name__)


def terms_of_service(request):
    template = 'NMTK_server/terms_of_service.html'
    site = get_current_site(request)
    terms_of_service = models.PageContent.objects.filter(
        page__name='terms_of_service')
    if terms_of_service:
        return render(request, template,
                      {'page_data': terms_of_service,
                       'site': site})
    else:
        raise Http404('Page does not exist!')


def registerUser(request):
    if not settings.REGISTRATION_OPEN:
        return HttpResponseRedirect(reverse('registration_disallowed'))
        return render(request,
                      'NMTK_server/registration_closed.html')
    template = 'NMTK_server/registration_form.html'
    site = get_current_site(request)
    # Returns 0 if there is no terms of service page content...
    terms_of_service = models.PageContent.objects.filter(
        page__name='terms_of_service').count()
    if request.method == 'POST':
        userform = forms.NMTKRegistrationForm(
            request.POST, tos=terms_of_service)
        if userform.is_valid():
            user = userform.save()
            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
            username = user.username
            if isinstance(user.username, unicode):
                username = username.encode('utf-8')
            activation_key = hashlib.sha1(salt + username).hexdigest()
            profile = registration_models.RegistrationProfile(
                user=user, activation_key=activation_key)
            profile.save()
            profile.send_activation_email(site, request)
            return render(request,
                          'NMTK_server/registration_complete.html')
    else:

        userform = forms.NMTKRegistrationForm(tos=terms_of_service)
    return render(request, template,
                  {'form': userform,
                   'site': site})


def nmtk_index(request, page_name='nmtk_index'):
    '''
    The function to display the NMTK Index page.  This is goverened by
    the NMTK_BANNER_OVERRIDE_URL setting - which might cause the
    splash page to be ignored.
    '''
    override_setting = getattr(settings, 'NMTK_BANNER_OVERRIDE_URL', None)
    if override_setting is None:
        data = models.PageContent.objects.filter(page__name='nmtk_index',
                                                 enabled=True)

        return render(request, 'NMTK_server/index.html',
                      {'registration_open': settings.REGISTRATION_OPEN,
                       'ui_installed': 'NMTK_ui' in settings.INSTALLED_APPS,
                       'page_data': data})
    elif override_setting == '':
        return nmtk_ui(request)
    else:
        return HttpResponseRedirect(override_setting)


def nmtk_ui(request):
    '''
    It's possible that the NMTK_ui is not enabled, but NMTK_server is
    - in such cases we cannot properly redirect the user from admin pages
    and the link to the UI, so instead we'll just give them the index page
    again - since that's all we can provide in this case.

    With this in mind, all the NMTK_server pages that refer to the UI use the
    nmtk_server_nmtk_ui named urlpattern, which is tied to this view, which
    redirects to the UI if it is installed/enabled.
    '''
    if 'NMTK_ui' in settings.INSTALLED_APPS:
        try:
            return HttpResponseRedirect(reverse('nmtk_ui_nmtk_ui'))
        except Exception as e:
            pass
    logger.info('NMTK_ui application is not enabled')
    return nmtk_index(request)


# Methods below are methods that are called by the tool to send results
# back to the server.  As a result, they are not user-facing, and do not
# need things like the login_required decorator.

@csrf_exempt
@authentication.requireValidAuthToken
@authentication.requireValidJobId
def updateStatus(request):
    '''
    Update the status of a job in the database.  In this case we
    expect there to be three keys in the json payload:
     - timestamp - a timestamp as to when the status update was
                   generated by the tool (ISO8601 formatted!)
     - status - a status message (max length 1024 bytes) to use to
                update the job status.
     - category - A category for the message, valid values are
                  Debug, Message, Warning, or Error (default is Message)
    '''
    logger.debug('Updating status for job id %s', request.NMTK_JOB.pk)
    json_data = json.loads(request.FILES['config'].read())
    logger.debug('Read updated status of %s', json_data)
    try:
        # Convert the client supplied category to one of our choice values.
        if json_data.has_key('category'):
            logger.debug('Key is there!')
            for k, v in models.JobStatus.CATEGORY_CHOICES:
                logger.debug(
                    'Check for match! %s, %s', v.lower(),
                    json_data['category'].lower())
                if v.lower() == json_data['category'].lower():
                    json_data['category'] = k
                    break
            else:
                logger.debug('Did not find matching status! using info')
                del json_data['category']
        # Parse the timestamp provided to a regular datetime value.
        if json_data.has_key('timestamp'):
            try:
                json_data['timestamp'] = dateutil.parser.parse(
                    json_data['timestamp'])
            except Exception, e:
                logger.error('Tool server passed in invalid timestamp data: %s',
                             json_data['timestamp'])
                del json_data['timestamp']
    except:
        json_data = {'status': data}
    # Some defaults to use for missing data.
    status_data = {'timestamp': timezone.now(),
                   'category': models.JobStatus.CATEGORY_STATUS}
    if (json_data.has_key('category') and
            json_data['category'] in (models.JobStatus.CATEGORY_SYSTEM,)):
        logger.info('Tool tried to set category to a system category!')
        status_data['category'] = models.JobStatus.CATEGORY_ERROR
    status_data.update(json_data)
    logger.debug('Final updated status is %s', status_data)

    status_m = models.JobStatus(message=status_data['status'],
                                timestamp=status_data['timestamp'],
                                job=request.NMTK_JOB,
                                category=status_data['category'])
    status_m.save()
    return HttpResponse(json.dumps({'status': 'Status added with key of %s' % (
        status_m.pk)}), content_type='application/json')


@csrf_exempt
@authentication.requireValidAuthToken
@authentication.requireValidJobId
def processResults(request):
    '''
    The idea here is that this URL always posts successful results, though
    in reality it probably ought to be enhanced to accept both success
    results as well as failure results.  We can worry about handling that
    based on content type.
    '''
    config = json.loads(request.FILES['config'].read())

    base_description = "Results from '{0}'".format(
        request.NMTK_JOB.description)
    if config['status'] == 'results':
        models.JobStatus(message='Received results from Tool Server',
                         timestamp=timezone.now(),
                         job=request.NMTK_JOB).save()
        if ('results' not in config or
                'field' not in config['results'] or
                'file' not in config['results']):
            logger.error('Results received with no valid results key ' +
                         'in config (old API?) (%s)', config)
            models.JobStatus(
                message='Unable to authenticate request from tool server.',
                timestamp=timezone.now(),
                job=request.NMTK_JOB).save()
            return HttpResponseServerError('Invalid result format')
        result_field = config['results']['field']
        result_field_units = field_units = None

        # field units can be an object also, in which case it's really
        # a set of fields and their units:
        if 'units' in config['results']:
            if isinstance(config['results']['units'], (str, unicode)):
                result_field_units = config['results']['units']
            else:
                try:
                    result_field_units = config['results'][
                        'units'].get(result_field, None)
                    field_units = config['results']['units']
                except Exception as e:
                    logger.debug('Failed to parse field units' +
                                 ', expected an object: %s', e)

        # the optional ordered list of fields, we require a list
        # of field names, and use a default of nothing if such a list isn't
        # provided.
        field_order = config['results'].get('field_order', None)
        if field_order is None:
            field_order = []
        elif not isinstance(field_order, (list, tuple),):
            logger.error('Result field_order should be a list or ' +
                         'tuple, not %s: %s', type(
                             field_order),
                         str(field_order))
            field_order = []
        logger.debug('Default field order is %s', field_order)
        # Now we have the field order provided by the tool itself
        # which we need to (eventually) augment with the fields from
        # the job itself.

        result_file = config['results']['file']

        if config['results']['file'] not in request.FILES:
            logger.error('Specified file for results was not uploaded')
            models.JobStatus(
                message='Tool server failed to upload required results file.',
                timestamp=timezone.now(),
                job=request.NMTK_JOB).save()
            return HttpResponseServerError('Invalid result file specified')
        total = len(request.FILES) - 1

        i = 0
        for namespace in request.FILES.keys():
            if namespace == 'config':
                continue
            i += 1
            if (total > 1):
                description = base_description + \
                    ' ({0} of {1} files)'.format(i, total)
            else:
                description = base_description
            kwargs = {}
            if namespace == result_file:
                primary = True
                field = result_field
            else:
                field = None
                primary = False
            result = models.DataFile(user=request.NMTK_JOB.user,
                                     name="job_{0}_results".format(
                                         request.NMTK_JOB.pk),
                                     # name=os.path.basename(request.FILES[result_file].name),
                                     description=description,
                                     content_type=request.FILES[
                                         namespace].content_type,
                                     type=models.DataFile.JOB_RESULT,
                                     fields=field_order,
                                     units=field_units,
                                     result_field=field,
                                     result_field_units=result_field_units)
            filename = os.path.basename(request.FILES[namespace].name)
            result.file.save(
                filename,
                ContentFile(
                    request.FILES[namespace].read()),
                save=False)

            if namespace == result_file:
                # Pass in the job here so that the data file processor knows to
                # update the job when this is done (only happens with primary
                # file.)
                result.save(job=request.NMTK_JOB)
            else:
                result.save()
            # Save the linkage back to the job...
            rf = models.ResultsFile(job=request.NMTK_JOB,
                                    datafile=result,
                                    primary=primary)
            rf.save()

        request.NMTK_JOB.status = request.NMTK_JOB.POST_PROCESSING
        request.NMTK_JOB.save()

        models.JobStatus(message='Post processing results file(s)',
                         timestamp=timezone.now(),
                         job=request.NMTK_JOB).save()
    elif config['status'] == 'error':
        logger.debug('config is %s', config)
        models.JobStatus(message='\n'.join(config['errors']),
                         timestamp=timezone.now(),
                         job=request.NMTK_JOB).save()
        request.NMTK_JOB.status = request.NMTK_JOB.FAILED
        request.NMTK_JOB.save()

    return HttpResponse(json.dumps({'status': 'Results saved'}),
                        content_type='application/json')


def logout_page(request):
    """
    Log users out and re-direct them to the main page.
    """
    logout(request)
    return HttpResponseRedirect('/')
