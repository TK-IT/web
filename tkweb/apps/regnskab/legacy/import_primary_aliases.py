import os
import sys
import json
import argparse
import datetime


def strptime(s):
    if s is not None:
        try:
            return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            return datetime.datetime.strptime(s + "+0100", "%Y-%m-%dT%H:%M:%S%z")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    with open(args.filename) as fp:
        data = json.load(fp)

    import_primary_aliases(data, sys.stdout)


def import_primary_aliases(data, fp):
    from tkweb.apps.regnskab.models import Alias, Profile

    profiles = {p.name: p for p in Profile.objects.all()}

    primary_ids = []
    for o in data:
        qs = Alias.objects.filter(
            root=o["root"],
            start_time=strptime(o["start_time"]),
            end_time=strptime(o["end_time"]),
        )
        qs = qs | Alias.objects.filter(
            root=o["root"], start_time=strptime(o["start_time"]), end_time=None
        )
        try:
            a = qs.get()
        except Alias.DoesNotExist:
            qs = Alias.objects.filter(root=o["root"])
            if qs:
                if len(qs) == 1:
                    print("%s %s: Adjust time" % (o["root"], a.id))
                    primary_ids.append(a.id)
                else:
                    print(
                        "%s: No exact match for %s; found %s"
                        % (
                            o["root"],
                            (o["start_time"], o["end_time"]),
                            [(a.start_time, a.end_time) for a in qs],
                        ),
                        file=fp,
                    )
            else:
                # print("%s: No such alias" % o['root'], file=fp)
                pass
        else:
            if a.profile.name != o["name"]:
                print(
                    "%s %s: Expected %s, found %s"
                    % (o["root"], a.id, o["name"], a.profile.name),
                    file=fp,
                )
            else:
                print("%s: %s" % (o["root"], a.id), file=fp)
            primary_ids.append(a.id)
    qs = Alias.objects.filter(id__in=primary_ids)
    print(qs, file=fp)
    qs.update(is_title=True)


if __name__ == "__main__":
    if os.path.exists("manage.py"):
        BASE_DIR = "."
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(BASE_DIR, "manage.py")) as fp:
        settings_line = next(
            l
            for l in fp
            if "DJANGO_SETTINGS_MODULE" in l and not l.strip().startswith("#")
        )
        eval(settings_line.strip())
    import django

    django.setup()
    main()
