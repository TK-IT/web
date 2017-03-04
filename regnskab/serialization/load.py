import sys
import json


def main():
    from .dump import RegnskabData
    cbs = RegnskabData().load(json.load(sys.stdin))
    for cb in cbs:
        if cb.objects:
            print('%s(%d\N{MULTIPLICATION SIGN} %s)...' %
                  (cb.__class__.__name__,
                   len(cb.objects),
                   cb.objects[0].__class__.__name__))
        cb()


if __name__ == '__main__':
    from .base import django_setup
    django_setup()
    main()
