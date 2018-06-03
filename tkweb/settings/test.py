# encoding: utf8
from tkweb.settings.base import *

SECRET_KEY = "This.is.not.a.secret.key"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# This is not used
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "../testdb.sqlite3"),
    }
}

# TEST_RUNNER = 'rainbowtests.test.runner.RainbowDiscoverRunner' # Fancy colors

RAINBOWTESTS_SHOW_MESSAGES = False


class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()
