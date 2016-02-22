from tkweb.settings.base import *

DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = True

SECRET_KEY = 'This.is.not.a.secret.key'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
