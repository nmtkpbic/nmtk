'''
Setup the site using information from settings.py
'''

from django.contrib.sites import models 
from django.db.models import signals 
from django.conf import settings

def create_site(app, created_models, verbosity, **kwargs):
    """
    Create the default site when when we install the sites framework
    """
    if models.Site in created_models:
        models.Site.objects.all().delete()

        site = models.Site()
        site.pk = getattr(settings, 'SITE_ID', 1)
        site.name = getattr(settings, 'SITE_NAME', 'NMTK Server')
        site.domain = getattr(settings, 'SITE_DOMAIN', 'nmtk.otg-nc.com')
        site.save()

signals.post_syncdb.connect(create_site, sender=models)