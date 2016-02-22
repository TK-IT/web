from tkweb.settings.base import *

DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = False

# Generate using pwgen -sy 50 1
SECRET_KEY = '...'

ALLOWED_HOSTS = []


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {}
