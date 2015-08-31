from django.conf import settings  # import the settings file


def registration_open(request):
    # return the value you want as a dictionary. you may add multiple values
    # in there.
    return {'REGISTRATION_OPEN': settings.REGISTRATION_OPEN}
