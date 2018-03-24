import os
import sys
import json
import argparse
import datetime


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

    import_aliases(data, sys.stdout)


def import_aliases(data, fp):
    from tkweb.apps.regnskab.models import Alias, Title, Profile
    profiles = {p.name: p for p in Profile.objects.all()}

    aliases = []
    for o in data:
        try:
            p = profiles[o['name']]
        except KeyError:
            continue
        aliases.append(
            Alias(profile=p, period=o['period'], root=o['root'],
                  start_time=strptime(o['start_time']),
                  end_time=strptime(o['end_time'])))

    def key(o):
        return (o.profile_id, o.root, o.period)

    existing = set()
    for o in list(Alias.objects.all()) + list(Title.objects.all()):
        existing.add(key(o))

    new = [o for o in aliases if key(o) not in existing]

    fp.write("Create %s aliases\n" % len(new))
    Alias.objects.bulk_create(new)


if __name__ == "__main__":
    if os.path.exists('manage.py'):
        BASE_DIR = '.'
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(BASE_DIR, 'manage.py')) as fp:
        settings_line = next(l for l in fp
                             if 'DJANGO_SETTINGS_MODULE' in l
                             and not l.strip().startswith('#'))
        eval(settings_line.strip())
    import django
    django.setup()
    main()
