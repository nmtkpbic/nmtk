# Create your views here.
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.conf import settings


@ensure_csrf_cookie
def nmtk_ui(request):
    return render(request, 'NMTK_ui/nmtk_ui.html',
                  {'production': settings.PRODUCTION})