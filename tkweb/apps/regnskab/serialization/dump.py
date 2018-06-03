import sys
import json


def debug_json_dump(data, path="data"):
    """
    In case json.dump raises a TypeError, this function will track down the
    paths to the unserializable objects.
    """
    if isinstance(data, list):
        for i, o in enumerate(data):
            debug_json_dump(o, path="%s[%s]" % (path, i))
    elif isinstance(data, dict):
        for k, o in data.items():
            debug_json_dump(o, path="%s[%r]" % (path, k))
    else:
        try:
            json.dumps(data)
        except TypeError as exn:
            print("%s: %r" % (path, exn), file=sys.stderr)


def main():
    from .base import django_setup

    django_setup()
    from .models import RegnskabData

    data = RegnskabData().dump()
    try:
        json.dump(data, sys.stdout, indent=2)
    except TypeError:
        debug_json_dump(data)
        raise


if __name__ == "__main__":
    main()
