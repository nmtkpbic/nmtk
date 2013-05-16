# Django settings for NMTK_apps project.
import os
import djcelery

BASE_PATH=os.path.dirname(__file__)
LOGFILE_PATH=os.path.abspath(os.path.join(BASE_PATH, '..','..','logs'))
DEBUG = False
TEMPLATE_DEBUG = DEBUG
djcelery.setup_loader()


ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(BASE_PATH,'nmtk.sqlite'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT=os.path.abspath(os.path.join('../..', 'htdocs/static'))

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'hk(f4*q-%yo9xf*x@_4#cv=wc8zp=%03=sukgl+_6sz2=zdmy='

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'NMTK_apps.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'NMTK_apps.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    #'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.sites',
    #'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'NMTK_tools', # An app used to generate a list of tools.
    'MN_model', # The tool for the Minnesota pedestrian/cycle models
    'SF_model', # The tool for the SF pedestrian model
    'NMTK_server', # A test NMTK server for NMTK validating tools locally.
    'djcelery',
    'kombu.transport.django',
)

# Define a GeoJSON serializer so we can serialize and return results of
# various tasks in the GeoJSON format.
SERIALIZATION_MODULES = { 'geojson' : 'NMTK_apps.serializers.geojson' }


# if you want to change the logging (to disable debug) do it here..
MIN_LOG_LEVEL='DEBUG' # 'INFO' for non-debug, 'DEBUG' for debugging

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
    
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'debug': {
            'level':'DEBUG',
            'class':'logging.handlers.WatchedFileHandler',
            'filename': os.path.join(LOGFILE_PATH,'django-debug.log'),
            'formatter':'standard',
        },  
        'default': {
            'level':'INFO',
            'class':'logging.handlers.WatchedFileHandler',
            'filename': os.path.join(LOGFILE_PATH,'django-request.log'),
            'formatter':'standard',
        },
        'apache': {
            'level':'INFO',
            'class':'logging.StreamHandler',
            'formatter':'standard',
        },
    },
    'loggers': {    
        '': {
            'handlers': ['debug', 'default'],
            'level': MIN_LOG_LEVEL,
            'propagate': True,
        },
        'django.request': { # Stop request debug from logging to main logger
            'handlers': ['apache'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db': { # We can turn on db logging by switching the handler to debug
            'handlers': ['null'],
            'level': MIN_LOG_LEVEL,
            'propagate': False,
        },
    }
}

# This dictionary is used by NMTK tools to interact with the NMTK server
# In particular, it stores the public/private keys for each tool, with the 
# expectation that the tool knows what it's "tool name" is (the outermost
# keys of the dictionary.)
#
# For the purposes of convenience here, the tool names match the app name
# in question.  That also makes things easier for the decorators, which
# rely on matches between the tool name and app name here.
#
# Note: by design if you are using the NMTK_server app (which is a 
# virtual NMTK server used for development) it won't use this data - it's for
# tools only.  The Server app will use it's database records for managing this.
# However, it's important to note that what's here, and what's in the DB should
# match or requests to/from the server will fail.

NMTK_KEYS={'MN_Model': {'public_key': 'd0461b9536eb483d9f23c157e809af35',
                        'private_key': '''yq@5u058y312%ebmyi85ytpfwjm9zv)1u2wu-m1s)%cngrvf_^'''},
           }


# The new config specification supports multiple NMTK servers.
# This means we identify the server and shared secret via the
# public key information that's part of the payload.
NMTK_SERVERS={'d0461b9536eb483d9f23c157e809af35': {'url': 'http://nmtk1.otg-nc.com/nmtk/server',
                                                   'secret': '''yq@5u058y312%ebmyi85ytpfwjm9zv)1u2wu-m1s)%cngrvf_^''' },
              'b17b46d6-763f-4292-bdc6-6a631883ee50': {'url': 'http://mutant.cgclientx.com:7878/',
                                                       'secret': '''$2a$10$/k4M0R1GGW0J6SFzobQKMe/jc/YUX0/JQ3ppBbr1NPQTTZsj1nU36''' },                                    
              }

BROKER_URL = 'django://'

