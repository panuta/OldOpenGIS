import os
_base = os.path.dirname(__file__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'
#DATABASE_NAME = 'opengis2'
#DATABASE_NAME = 'opengis_platform'
DATABASE_NAME = 'opengis_dev'
DATABASE_USER = 'panuta'
DATABASE_PASSWORD = 'panuta'
DATABASE_HOST = ''
DATABASE_PORT = ''

TIME_ZONE = 'Asia/Bangkok'

SITE_ID = 1

LANGUAGE_CODE = 'en-us'
USE_I18N = True

LOGIN_REDIRECT_URL = "/my/"

MEDIA_ROOT = os.path.join(_base, "media") + "/"
#MEDIA_ROOT = "/Users/apple/Projects/OpenGIS/Platform/opengis_platform/media/"
MEDIA_URL = 'http://localhost:8000/m'
# MEDIA_URL = 'http://10.0.1.58:8000/m'

ADMIN_MEDIA_PREFIX = '/media/'

SECRET_KEY = '32j0k*!2(2&_75f5o7z!z9c6ho+@+u@q&gsyb8!(d3bq3@bq32'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.middleware.transaction.TransactionMiddleware',
	'opengis_platform.middleware.AJAXSimpleExceptionResponse',
	'opengis_platform.middleware.OpenGISExceptionMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
	'django.core.context_processors.request',
	'django.core.context_processors.auth',
	'django.core.context_processors.debug',
	'django.core.context_processors.i18n',
	'django.core.context_processors.media',
)

ROOT_URLCONF = 'opengis_platform.urls'

TEMPLATE_DIRS = (
	os.path.join(_base, "templates"),
)

ACCOUNT_ACTIVATION_DAYS = 7

SYSTEM_USERNAME = 'system'
SYSTEM_EMAIL_ADDRESS = 'application.testbed@gmail.com'
SYSTEM_PASSWORD = 'panuta'

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'application.testbed@gmail.com'
EMAIL_HOST_PASSWORD = 'opendream'
EMAIL_PORT = 587

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
	'django.contrib.gis',
	'django.contrib.admin',
	'registration',
	'opengis',
)

# GeoDjango
TEST_RUNNER = 'django.contrib.gis.tests.run_tests'
POSTGIS_TEMPLATE = 'template_for_postgis'

# OpenGIS
OPENGIS_TEMPLATE_PREFIX = "./opengis/"
TEMP_CSV_PATH = os.path.join(_base, "files/csv")

MAIN_APPLICATION_NAME = "opengis"
USER_TABLE_PREFIX = "ut"

