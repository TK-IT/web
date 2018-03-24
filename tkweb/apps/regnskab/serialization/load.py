import sys
import json
import argparse


ALLOW_NUKE_HOSTS = ['alcyone']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nuke-database-before-loading',
                        action='store_true', dest='nuke')
    args = parser.parse_args()

    from .base import django_setup
    django_setup()
    from .models import RegnskabData
    cbs = RegnskabData().load(json.load(sys.stdin))

    if args.nuke:
        from socket import gethostname

        hostname = gethostname()
        if hostname not in ALLOW_NUKE_HOSTS:
            raise Exception("You need to add %r to ALLOW_NUKE_HOSTS." %
                            hostname)

        import regnskab.models
        models = '''Transaction Purchase PurchaseKind Sheet Session Title Alias
        SheetStatus Profile Email EmailTemplate'''.split()
        # Ensure all models actually exist before deleting anything
        model_types = [getattr(regnskab.models, n) for n in models]

        for model in model_types:
            print(model.__name__, model.objects.all().delete())

    for cb in cbs:
        if cb.objects:
            print('%s(%d\N{MULTIPLICATION SIGN} %s)...' %
                  (cb.__class__.__name__,
                   len(cb.objects),
                   cb.objects[0].__class__.__name__))
        cb()


if __name__ == '__main__':
    main()
