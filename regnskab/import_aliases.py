import os
import sys
import json
import argparse
import datetime


def get_profiles_without_aliases():
    from regnskab.models import Profile
    return {p.name: p for p in Profile.objects.filter(alias=None)}


def strptime(s):
    if s is not None:
        try:
            return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S%z')
        except ValueError:
            return datetime.datetime.strptime(s+'+0100', '%Y-%m-%dT%H:%M:%S%z')


def main():
    from regnskab.models import Alias
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()

    with open(args.filename) as fp:
        data = json.load(fp)

    profiles = get_profiles_without_aliases()
    aliases = []
    for o in data:
        try:
            p = profiles[o['name']]
        except KeyError:
            continue
        aliases.append(
            Alias(profile=p, period=None, root=o['alias'],
                  start_time=strptime(o['start_time']),
                  end_time=strptime(o['end_time'])))
    print("Create %s aliases" % len(aliases))
    Alias.objects.bulk_create(aliases)


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(BASE_DIR, 'venv/lib/python3.5/site-packages'))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "regnskab.settings")
    import django
    django.setup()
    main()
