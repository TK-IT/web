import os
import sys
import django


def django_setup():
    if os.path.exists('manage.py'):
        BASE_DIR = '.'
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(BASE_DIR, 'venv/lib/python3.6/site-packages'))
    with open(os.path.join(BASE_DIR, 'manage.py')) as fp:
        settings_line = next(l for l in fp
                             if 'DJANGO_SETTINGS_MODULE' in l)
        eval(settings_line.strip())
    django.setup()
