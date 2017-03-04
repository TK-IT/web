import os
import sys
import glob
import django


def django_setup():
    if os.path.exists('manage.py'):
        BASE_DIR = '.'
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.extend(
        glob.glob(os.path.join(BASE_DIR, 'venv/lib/*/site-packages')))
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        with open(os.path.join(BASE_DIR, 'manage.py')) as fp:
            settings_line = next(l for l in fp
                                 if 'DJANGO_SETTINGS_MODULE' in l)
            eval(settings_line.strip())
    django.setup()
