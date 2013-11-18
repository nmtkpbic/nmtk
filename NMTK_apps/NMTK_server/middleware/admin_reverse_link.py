import re
import logging
logger=logging.getLogger(__name__)
from django.core.urlresolvers import reverse
# Mostly copied from http://stackoverflow.com/questions/9873582/adding-link-to-django-admin-page,
# but changed so it works regardless of the location of the admin page(s) by chander

ADMIN_URL=reverse('admin:index')
UI_URL=reverse('nmtk_server_nmtk_ui')
class AdminReverseURI(object):
    def is_admin_url(self, url):
        if url.startswith(ADMIN_URL):
            return True
        return False

    def process_request(self, request):
        if self.is_admin_url(request.path) and \
            not self.is_admin_url(request.META.get('HTTP_REFERER','')):
            request.session['last_site_url'] = request.META.get('HTTP_REFERER',UI_URL)