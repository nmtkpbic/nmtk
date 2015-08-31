from django.contrib.auth import logout


class StrictAuthentication:
    '''
    Taken from: http://djangosnippets.org/snippets/1105/
    When a user is marked as inactive, their login sessions are logged out,
    thereby forcing logout for inactive users immediately after they are
    marked as inactive.
    '''

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated() and not request.user.is_active:
            logout(request)
