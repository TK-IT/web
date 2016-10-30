import os
import sys
import json
import argparse
import datetime


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
        for o in objects:
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
            for o in new:
                o.save()
    if only_new:
        return new
    else:
        return new + existing


def filter_related(parent_objects, related_objects, related_field):
    parent_objects = set(parent_objects)
    new = []
    for o in related_objects:
        r = getattr(o, related_field)
        if r.pk and r in parent_objects:
            setattr(o, related_field, r)
            new.append(o)
    return new


def get_profiles(data):
    from regnskab.models import Profile
    emails = {}
    for o in data:
        emails.update(o['emails'])
    return [Profile(name=name, email=email) for name, email in emails.items()]


def make_profiles(data):
    profiles = get_profiles(data)
    profiles = save_all(profiles, ['name'])
    return {p.name: p for p in profiles}


def get_emails(data, profiles):
    from regnskab.models import Email, EmailVariable
    emails = []
    email_variables = []

    purchase_kind_email_var = dict(
        oel='OEL', xmas='GULD', kasser='KASSER', vand='VAND')

    for o in data:
        time = datetime.datetime.strptime(o['time'], '%Y-%m-%dT%H:%M:%S%z')
        v_prices = {}
        for i, kind in enumerate(o['kinds']):
            v_prices['P' + purchase_kind_email_var[kind['key']]] = (
                '%.2f' % kind['price'])
        for k in o['names']:
            variables = dict(
                TITEL=o['titles'].get(k, ''),
                NAVN=o['names'][k],
                EMAIL=o['emails'][k],
                **v_prices)
            for key, count in o['purchases'].get(k, {}).items():
                if key == 'kasser':
                    v = '%.1f' % count
                else:
                    v = '%d' % count
                variables[purchase_kind_email_var[key]] = v
            variables['ANDET'] = '%.2f' % o['others'].get(k, 0)
            variables['BETALT'] = '%.2f' % o['payments'].get(k, 0)

            emails.append(Email(
                profile=profiles[k],
                time=time,
                recipient_name=o['names'][k],
                recipient_email=o['names'][k]))
            for k, v in variables.items():
                try:
                    f = float(v)
                except ValueError:
                    f = None
                email_variables.append(EmailVariable(
                    email=emails[-1],
                    key=k,
                    value=v,
                    numeric_value=f))

    return emails, email_variables


def get_payments(data, profiles):
    from regnskab.models import Payment
    payments = []

    for o in data:
        time = datetime.datetime.strptime(o['time'], '%Y-%m-%dT%H:%M:%S%z')
        for name, amount in o['payments'].items():
            payments.append(
                Payment(profile=profiles[name],
                        time=time,
                        amount=amount))
        for name, amount in o['others'].items():
            payments.append(
                Payment(profile=profiles[name],
                        time=time,
                        amount=-amount,
                        note='Andet'))
    return payments


def get_sheets(data, profiles):
    from regnskab.models import Sheet, SheetRow, PurchaseKind, Purchase
    sheets = []
    purchase_kinds = []
    rows = []
    purchases = []
    for o in data:
        time = datetime.datetime.strptime(o['time'], '%Y-%m-%dT%H:%M:%S%z')
        sheet = Sheet(start_date=time.date(), end_date=time.date())
        sheets.append(sheet)
        kind_map = {}
        for i, kind in enumerate(o['kinds']):
            purchase_kinds.append(PurchaseKind(
                sheet=sheet,
                position=i+1,
                name=kind['name'],
                price=kind['price']))
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
    from regnskab.models import EmailVariable, Purchase
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()

    with open(args.filename) as fp:
        data = json.load(fp)

    profiles = make_profiles(data)
    emails, email_variables = get_emails(data, profiles)
    payments = get_payments(data, profiles)
    sheets, purchase_kinds, rows, purchases = get_sheets(data, profiles)
    print("%s rows" % len(rows))

    emails = save_all(emails, unique_attrs=('profile', 'time'), only_new=True)
    EmailVariable.objects.bulk_create(
        filter_related(emails, email_variables, 'email'))
    save_all(payments, unique_attrs=('profile', 'time'), bulk=True)

    sheets = save_all(sheets, unique_attrs=('start_date', 'end_date'),
                      only_new=True)
    purchase_kinds = filter_related(sheets, purchase_kinds, 'sheet')
    purchase_kinds = save_all(purchase_kinds, unique_attrs=('sheet', 'name'),
                              only_new=True)
    rows = filter_related(sheets, rows, 'sheet')
    print("%s rows" % len(rows))
    rows = save_all(rows, unique_attrs=('sheet', 'name', 'profile'),
                    only_new=True)
    purchases = filter_related(purchase_kinds, purchases, 'kind')
    purchases = filter_related(rows, purchases, 'row')
    Purchase.objects.bulk_create(purchases)


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(BASE_DIR, 'venv/lib/python3.5/site-packages'))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "regnskab.settings")
    import django
    django.setup()
    main()
