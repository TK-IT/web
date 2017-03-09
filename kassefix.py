import os
import re
import sys
import argparse
import datetime

from decimal import Decimal
from fractions import Fraction


PERIOD = 2016


def initialize_django():
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        with open('manage.py') as fp:
            mo = re.search(
                r'^\s*os\.environ\.setdefault\("DJANGO_SETTINGS_MODULE", ' +
                r'"([^\\"]+)"\)', fp.read(), re.M)
        os.environ['DJANGO_SETTINGS_MODULE'] = mo.group(1)

    try:
        import django
    except ImportError:
        if sys.prefix == '/usr':
            if os.path.exists('venv/bin/activate'):
                os.execl('/bin/bash', 'bash', '-c',
                         'set -e; . venv/bin/activate; exec python "$@"',
                         'bash', *sys.argv)
            else:
                raise ImportError(
                    'Couldn\'t import Django. Do you need to enter a ' +
                    'virtual environment?')
        raise

    django.setup()


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    initialize_django()

    from regnskab.models import (
        Sheet, PurchaseKind, SheetRow, Purchase, Transaction,
    )

    # There's no way I'm fixing all the old data
    # qs = Sheet.objects.filter(end_date__gte=datetime.datetime(2014, 1, 9))
    qs = Sheet.objects.filter(period=PERIOD)
    qs1 = Sheet.objects.filter(session=None, period=PERIOD)
    qs2 = Sheet.objects.filter(period=PERIOD).exclude(session=None)
    all_kinds = {kind.id: kind for kind in PurchaseKind.objects.all()}
    assert all(kind.unit_price % 1 == 0 for kind in all_kinds.values())

    sheet_kinds = {}
    rel_qs = PurchaseKind.sheets.through.objects.all()
    for k, s in rel_qs.values_list('purchasekind_id', 'sheet_id'):
        sheet_kinds.setdefault(s, []).append(all_kinds[k])

    old_kind_map = {}
    for sheet in qs1:
        for kind in sheet_kinds[sheet.id]:
            key = kind.unit_price
            if old_kind_map.setdefault(key, kind) is not kind:
                raise KeyError(key)

    new_kind_map = {}
    for sheet in qs2:
        for kind in sheet_kinds[sheet.id]:
            key = kind.unit_price
            if new_kind_map.setdefault(key, kind) is not kind:
                raise KeyError(key)

    if old_kind_map != new_kind_map:
        translate = {old_kind.id: new_kind_map[price].id
                     for price, old_kind in old_kind_map.items()}
        translate = {o: n for o, n in translate.items() if o != n}
        assert not (set(translate.keys()) & set(translate.values())), translate
        print('from regnskab.models import *')
        print('qs = Purchase.objects.filter(row__sheet__period=%s)' % PERIOD)
        for old, new in translate.items():
            print('qs.filter(kind_id=%s).update(kind_id=%s)' % (old, new))
        print('qs = PurchaseKind.sheets.through.objects.' +
              'filter(sheet__period=%s)' % PERIOD)
        for old, new in translate.items():
            print('qs.filter(purchasekind_id=%s)' % old +
                  '.update(purchasekind_id=%s)' % new)
        for p in new_kind_map.keys() - old_kind_map.keys():
            for s in qs1.values_list('id', flat=True):
                print('PurchaseKind.sheets.through.objects.create(' +
                      'purchasekind_id=%s, sheet_id=%s)' %
                      (new_kind_map[p].id, s))
        return
    all_rows = {row.id: row for row in SheetRow.objects.all()}
    sheet_purchases = {}
    purchase_qs = Purchase.objects.all()
    for p in purchase_qs:
        p.row = all_rows[p.row_id]
        sheet_purchases.setdefault(p.row.sheet_id, []).append(p)

    kind_names = {'øl', 'guldøl', 'sodavand',
                  'ølkasse', 'guldølkasse', 'sodavandkasse'}

    fixes = {
        Decimal('1.4'): (1, 0, 0.5, 0),
        Decimal('1.68'): (1, 0.5, 0, 0),
        Decimal('2.72'): (0, 2, 0, 0),
        Decimal('3.18'): (2.5, 0.5, 0, 0),
        Decimal('3.36'): (2, 1, 0, 0),
        Decimal('3.68'): (3, 0.5, 0, 0),
        Decimal('1.34'): (0, 1, 0, -5),
    }
    assert all(len(str(Decimal(v))) <= 3
               for fix in fixes.values() for v in fix)

    print('import datetime')
    print('from regnskab.models import *')
    for sheet in qs:
        transaction_time = (
            sheet.end_date.year, sheet.end_date.month,
            sheet.end_date.day)
        kinds = {kind.name: kind for kind in sheet_kinds[sheet.id]}
        assert set(kinds.keys()) == kind_names
        prices = {name: int(kind.unit_price) for name, kind in kinds.items()}
        ølkasse = prices['ølkasse']
        guldkasse = prices['guldølkasse']
        vandkasse = prices['sodavandkasse']
        guldratio = Fraction(guldkasse, ølkasse)
        vandratio = Fraction(vandkasse, ølkasse)
        for p in sheet_purchases.get(sheet.id, ()):
            p.kind = all_kinds[p.kind_id]
            p.row = all_rows[p.row_id]
            if p.kind.name != 'ølkasse':
                continue
            if p.count % Decimal('0.5') == 0:
                continue
            print('Purchase.objects.filter(kind_id=%s, ' % p.kind_id +
                  'count=%r, row_id=%s).delete()' % (p.count, p.row_id))
            current_price = p.count * p.kind.unit_price
            *fix, correction = fixes[p.count]
            fix_kinds = 'ølkasse guldølkasse sodavandkasse'.split()
            fixed = [
                Purchase(kind=kinds[name], count=c)
                for c, name in zip(fix, fix_kinds) if c]
            for f in fixed:
                f.amount = Decimal(f.count) * f.kind.unit_price
                print('Purchase.objects.create(kind_id=%s, ' % f.kind_id +
                      'count=%r, row_id=%s)' % (f.count, p.row_id))
            if correction:
                fixed.append(
                    Transaction(profile_id=p.row.profile_id,
                                kind=Transaction.CORRECTION,
                                amount=correction))
                print('Transaction.objects.create(' +
                      'session_id=%r, ' % sheet.session_id +
                      'profile_id=%s, ' % p.row.profile_id +
                      'kind=Transaction.CORRECTION, ' +
                      'amount=%r, ' % correction +
                      'time=datetime.datetime(%s, %s, %s), ' %
                      transaction_time +
                      'period=%s)' % PERIOD)
            new_price = sum(f.amount for f in fixed)
            assert current_price == new_price

            print('#', sheet.end_date,
                  p.row.profile_id,
                  p.count,
                  correction, fixed)


if __name__ == "__main__":
    main()
