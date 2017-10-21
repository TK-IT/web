# encoding: utf8
from __future__ import unicode_literals
from tkweb.settings.base import *

# https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = False

# Generate using pwgen -sy 50 1
SECRET_KEY = 'ThisIsNotASecret'

ALLOWED_HOSTS = [
    '*',
]


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

# Update database configuration with $DATABASE_URL.
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(conn_max_age=500)
    }


ADMINS = (
    ('John Doe', 'webmaster@example.com'),
)

# Media files

MEDIA_ROOT = '/Pictures/tkammer/media/'

# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(name)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.join(BASE_DIR, '../django.log'),
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'mail_admins'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'WARNING'),
        },
        'tkweb': {
            'handlers': ['file', 'mail_admins'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}

# Cookies
# -------

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
