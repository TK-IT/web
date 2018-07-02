import os
import sys
import json
import argparse
import datetime


def get_profiles_without_data():
    from tkweb.apps.regnskab.models import Profile
    return {p.name: p for p in Profile.objects.filter(sheetstatus=None)}


def strptime(s):
    if s is not None:
        try:
            return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S%z')
        except ValueError:
            return datetime.datetime.strptime(s+'+0100', '%Y-%m-%dT%H:%M:%S%z')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()

    with open(args.filename) as fp:
        data = json.load(fp)

    import_statuses(data, sys.stdout)


def import_statuses(data, fp):
    from tkweb.apps.regnskab.models import SheetStatus
    profiles = get_profiles_without_data()
    objects = []
    for o in data:
        try:
            p = profiles[o['name']]
        except KeyError:
            continue
        objects.append(
            SheetStatus(profile=p,
                        start_time=strptime(o['start_time']),
                        end_time=strptime(o['end_time'])))
    fp.write("Create %s statuses\n" % len(objects))
    SheetStatus.objects.bulk_create(objects)


if __name__ == "__main__":
    if os.path.exists('manage.py'):
        BASE_DIR = '.'
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(BASE_DIR, '.venv/lib/python3.5/site-packages'))
    with open(os.path.join(BASE_DIR, 'manage.py')) as fp:
        settings_line = next(l for l in fp
                             if 'DJANGO_SETTINGS_MODULE' in l)
        eval(settings_line.strip())
    import django
    django.setup()
    main()
