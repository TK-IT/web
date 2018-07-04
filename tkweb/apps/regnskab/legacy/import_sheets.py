import os
import sys
import json
import argparse
import datetime


class Helper:
    stdout = sys.stdout
    stderr = sys.stderr

    @staticmethod
    def progress(elements, n=None):
        if n is None:
            elements = list(elements)
            n = len(elements)
        w = len(str(n))
        for i, x in enumerate(elements):
            print('\r\x1B[K(%s/%s) %s' % (str(i+1).rjust(w), n, x), end='')
            yield x
        print('')

    @staticmethod
    def save_all(objects, unique_attrs=None, only_new=False, bulk=False):
        if not objects:
            return []
        existing = []
        new = []
        if unique_attrs:
            unique_attrs = tuple(unique_attrs)

            def key(o):
                return tuple(getattr(o, k) for k in unique_attrs)

            main_model = type(objects[0])
            existing_dict = {key(o): o for o in main_model.objects.all()}
            for o in Helper.progress(objects):
                try:
                    e = existing_dict[key(o)]
                except KeyError:
                    new.append(o)
                else:
                    existing.append(e)
        else:
            new.extend(objects)

        if new:
            print("Save %s %s objects" % (len(new), type(new[0]).__name__))
            if bulk:
                type(new[0]).objects.bulk_create(new)
            else:
                if type(new[0]).objects.all().exists() or not unique_attrs:
                    for o in Helper.progress(new):
                        o.save()
                else:
                    # No objects exist in database,
                    # so we might just bulk insert them
                    # and retrieve the pks in bulk.
                    type(new[0]).objects.bulk_create(new)
                    pks = {key(o): o.id for o in type(new[0]).objects.all()}
                    for o in new:
                        o.id = pks[key(o)]
        if only_new:
            return new
        else:
            return new + existing

    @staticmethod
    def filter_related(parent_objects, related_objects, related_field):
        parent_objects = set(parent_objects)
        new = []
        for o in Helper.progress(related_objects):
            r = getattr(o, related_field)
            if r.pk and r in parent_objects:
                setattr(o, related_field, r)
                new.append(o)
        return new


def get_profiles(data):
    from tkweb.apps.regnskab.models import Profile
    emails = {}
    for o in data:
        emails.update(o['emails'])
    return [Profile(name=name, email=email if '@' in email else '')
            for name, email in emails.items()]


def make_profiles(data, save_all):
    profiles = get_profiles(data)
    profiles = save_all(profiles, ['name'])
    return {p.name: p for p in profiles}


def get_existing_profiles(data, helper):
    from tkweb.apps.regnskab.models import Profile
    profiles = get_profiles(data)
    existing = {p.name: p for p in Profile.objects.all()}
    existing_email = [(p.name, p.email, existing.get(p.name, Profile(email=None)).email)
                      for p in profiles]
    wrong_email = [x for x in existing_email
                   if x[2] is not None and x[1] != x[2]]
    if wrong_email:
        with open('wrong-email.json', 'w') as fp:
            json.dump(wrong_email, fp, indent=2)
        helper.stderr.write("Wrong emails written to wrong-email.json\n")
    new = sorted((name, email) for name, email, e in existing_email
                 if e is None)
    if new:
        with open('new-profiles.json', 'w') as fp:
            json.dump(new, fp, indent=2)
        helper.stderr.write("Unknown profiles written to new-profiles.json\n")
        raise Exception("Unknown profiles")
    return {p.name: existing[p.name] for p in profiles}


def strptime(s):
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError:
        return datetime.datetime.strptime(s+'+0100', '%Y-%m-%dT%H:%M:%S%z')


def get_transactions(data, profiles):
    transactions = []

    for o in data:
        raise NotImplementedError('Transaction.period needs to be populated')
        time = strptime(o['time'])
        for name, amount in o['payments'].items():
            transactions.append(
                Transaction(kind=Transaction.PAYMENT,
                            profile=profiles[name],
                            time=time,
                            amount=-amount))
        for name, amount in o['others'].items():
            transactions.append(
                Transaction(kind=Transaction.PURCHASE,
                            profile=profiles[name],
                            time=time,
                            amount=amount))
        for name, amount in o['corrections'].items():
            transactions.append(
                Transaction(kind=Transaction.CORRECTION,
                            profile=profiles[name],
                            time=time,
                            amount=amount))
    return transactions


purchase_kind_names = dict(oel='øl', xmas='guldøl', vand='sodavand',
                           kasser='ølkasser')


def get_sheets(data, profiles):
    from tkweb.apps.regnskab.models import Sheet, SheetRow, Purchase
    sheets = []
    purchase_kinds = []
    rows = []
    purchases = []
    for o in data:
        time = strptime(o['time'])
        sheet = Sheet(start_date=time.date(), end_date=time.date(),
                      period=o['period'])
        sheets.append(sheet)
        kind_map = {}
        for i, kind in enumerate(o['kinds']):
            name = purchase_kind_names[kind['key']]
            raise NotImplementedError('PurchaseKind.sheet no longer exists')
            purchase_kinds.append(PurchaseKind(
                sheet=sheet,
                position=i+1,
                name=name,
                unit_price=kind['price']))
            kind_map[kind['key']] = purchase_kinds[-1]
        for i, name in enumerate(sorted(o['purchases'])):
            row = SheetRow(sheet=sheet, profile=profiles[name], position=i + 1)
            rows.append(row)
            for k, v in o['purchases'][name].items():
                purchases.append(Purchase(
                    row=row,
                    kind=kind_map[k],
                    count=v))
    return sheets, purchase_kinds, rows, purchases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()

    with open(args.filename) as fp:
        data = json.load(fp)

    import_sheets(data, Helper)


def import_profiles(data, helper):
    make_profiles(data, helper.save_all)


def import_sheets(data, helper):
    save_all = helper.save_all
    filter_related = helper.filter_related

    profiles = get_existing_profiles(data, helper)
    transactions = get_transactions(data, profiles)
    sheets, purchase_kinds, rows, purchases = get_sheets(data, profiles)

    save_all(transactions, unique_attrs=('profile', 'time', 'kind'), bulk=True)

    sheets = save_all(sheets, unique_attrs=('start_date', 'end_date'),
                      only_new=True)
    raise NotImplementedError('PurchaseKind.sheet no longer exists')
    purchase_kinds = filter_related(sheets, purchase_kinds, 'sheet')
    purchase_kinds = save_all(purchase_kinds, unique_attrs=('sheet', 'name'),
                              only_new=True)
    rows = filter_related(sheets, rows, 'sheet')
    rows = save_all(rows, unique_attrs=('sheet', 'name', 'profile'),
                    only_new=True)
    purchases = filter_related(purchase_kinds, purchases, 'kind')
    purchases = filter_related(rows, purchases, 'row')
    helper.stdout.write("Create %s purchases\n" % len(purchases))
    Purchase.objects.bulk_create(purchases)


if __name__ == "__main__":
    if os.path.exists('manage.py'):
        BASE_DIR = '.'
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(BASE_DIR, '.venv/lib/python3.6/site-packages'))
    with open(os.path.join(BASE_DIR, 'manage.py')) as fp:
        settings_line = next(l for l in fp
                             if 'DJANGO_SETTINGS_MODULE' in l)
        eval(settings_line.strip())
    import django
    django.setup()
    main()
