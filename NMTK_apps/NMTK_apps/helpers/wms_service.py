from django.http import HttpResponse
import subprocess

def handleWMSRequest(request, job):
    response=HttpResponse
    pipe = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
