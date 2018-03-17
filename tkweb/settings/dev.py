# encoding: utf8
from __future__ import unicode_literals
from tkweb.settings.base import *

DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = True
THUMBNAIL_DEBUG = True

SECRET_KEY = 'This.is.not.a.secret.key'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '../db.sqlite3'),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(name)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'WARNING'),
        },
        'tkweb': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
    },
}

WIKI_CACHE_TIMEOUT = 0
