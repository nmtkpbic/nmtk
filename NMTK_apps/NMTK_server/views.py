# Create your views here.
from django.shortcuts import render
from NMTK_server import forms
from NMTK_server import models
from NMTK_server.decorators import authentication
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import logging
import collections
from django.core.files.base import ContentFile
import datetime
import tempfile
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout

logger=logging.getLogger(__name__)

@login_required
@user_passes_test(lambda u: u.is_active)
def downloadResults(request, job_id):
    try:
        job=models.Job.objects.get(job_id=job_id,
                                   user=request.user)
    except:
        raise Http404
    response = HttpResponse(job.results.file, content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename=result.geojson'
    return response

@login_required
@user_passes_test(lambda u: u.is_active)
def viewResults(request, job_id):
    try:
        job=models.Job.objects.get(job_id=job_id,
                                   user=request.user)
    except:
        raise Http404
    result=json.loads(job.results.read())
    table={}
    table['headers']=result['features'][0]['properties'].keys()
    table['rows']=[]
    for row in result['features']:
        this_row=[]
        for field in table['headers']:
            this_row.append(row['properties'][field])
        this_row.append(','.join(map(str,row['geometry']['coordinates'])))
        table['rows'].append(this_row)        
    table['headers'].append('Geometry')
    logger.debug('Done generating table structure for template.')
    return render(request, 'NMTK_server/display_results.html',
                  {'table': table,
                   'job_id': job_id })

@login_required
@user_passes_test(lambda u: u.is_active)
def refreshStatus(request, job_id):
    try:
        m=models.JobStatus.objects.filter(job=job_id,
                                          user=request.user)[0]
    except:
        logger.debug('No status reports received yet.')
        fakeStatus=collections.namedtuple('FakeStatus',['message',
                                                        'timestamp'])
        m=fakeStatus('Pending',datetime.datetime.now())
    result={'status': m.message,
            'timestamp': m.timestamp.isoformat()}
    return HttpResponse(json.dumps(result),
                        content_type='application/json')

@login_required
@user_passes_test(lambda u: u.is_active)
def configureJob(request, job=None):
    '''
    Build a form that can be used to configure a job to be sent to the 
    NMTK tool for processing.  In this case, we need to provide the field
    mappings, as well as the other parameters that the job requires for 
    processing.  If the result is valid, we'll send the whole thing over 
    to the NMTK tool for processing.
    
    If the form is submitted with all the parameters correctly, then
    the result is saved into the configuration for the job (serialized
    as json), and then the job is submitted to the tool for processing 
    (this happens automatically when the status of the job is set to
    Active).
    '''
    if request.POST.has_key('job_id'):
        try:
            job=models.Job.objects.get(pk=request.POST['job_id'],
                                       user=request.user)
            logger.debug('Retrieved job %s from form data.', job.pk)
        except:
            raise Http404
    elif job:
        form=forms.ToolConfigForm(job=job)
        
        
    if request.POST.has_key('job_id'):
        form=forms.ToolConfigForm(request.POST, job=job)
        if form.is_valid():
            logger.debug('HOORAY - form is valid!!!')
            job.config=form.cleaned_data
            job.status='A'
            job.user=request.user
            job.save()
            return render(request, "NMTK_server/result.html",
                          {'job_id': job.pk})
        
    return render(request, 'NMTK_server/job_config.html',
                  { 'job': job,
                    'form': form, })
@login_required
@user_passes_test(lambda u: u.is_active)
def submitJob(request):
    datafile=None
    initial={}
    if request.method == 'POST':
        datafile_form=forms.DataFileForm(request.POST,request.FILES)
        # We aren't too concerned about this file..if they provide a file,
        # we can save it here.
        if datafile_form.is_valid():
            datafile=datafile_form.save(commit=False)
            datafile.name=request.FILES['file'].name
            datafile.content_type=request.FILES['file'].content_type
            datafile.user=request.user
            datafile.save()
            job_form=forms.JobSubmissionFormTool(request.user, request.POST)
        else:
            job_form=forms.JobSubmissionForm(request.user,
                                             request.POST)
        if job_form.is_valid():
            job=job_form.save(commit=False)
            if 'data_file' not in job_form.cleaned_data:
                job.data_file=datafile
            job.user=request.user
            job.save()
            return configureJob(request, job)            
    else:
        job_form=forms.JobSubmissionForm(request.user)
        datafile_form=forms.DataFileForm()
    return render(request, 'NMTK_server/submitjob.html',
                  {'job_form': job_form,
                   'datafile_form': datafile_form })
    
    
# Methods below are methods that are called by the tool to send results
# back to the server.  As a result, they are not user-facing, and do not
# need things like the login_required decorator.
    
@csrf_exempt
@authentication.requireValidAuthToken
@authentication.requireValidJobId
def updateStatus(request):
    '''
    Update the status of a job in the database.  In this case we 
    expect there to be two keys in the json payload:
     - timestamp - a timestamp as to when the status update was
                   generated by the tool
     - status - a status message (max length 1024 bytes) to use to 
                update the job status.
    '''
    logger.debug('Updating status for job id %s', request.NMTK_JOB)
    data=request.FILES['data'].read()
    
    status_m=models.JobStatus(message=data,
                              timestamp=datetime.datetime.now(),
                              job=request.NMTK_JOB)
    status_m.save()
    return HttpResponse(json.dumps({'status': 'Status added with key of %s' % (status_m.pk)}),
                        content_type='application/json')

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
    config=json.loads(request.FILES['config'].read())
    data=ContentFile(request.FILES['data'].read())
    request.NMTK_JOB.results.save('results', data)
    if config['status'] == 'results':
        request.NMTK_JOB.status=request.NMTK_JOB.COMPLETE
    elif config['status'] == 'error':
        request.NMTK_JOB.status=request.NMTK_JOB.FAILED
    request.NMTK_JOB.save()
    models.JobStatus(message='COMPLETE',
                     timestamp=datetime.datetime.now(),
                     job=request.NMTK_JOB).save()
    return HttpResponse(json.dumps({'status': 'Results saved'}),
                        content_type='application/json')    
    
def logout_page(request):
    """
    Log users out and re-direct them to the main page.
    """
    logout(request)
    return HttpResponseRedirect('/')