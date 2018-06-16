from django.db import migrations, models


def coalesce_kinds(apps, schema_editor):
    PurchaseKind = apps.get_model('regnskab', 'PurchaseKind')
    Purchase = apps.get_model('regnskab', 'Purchase')
    kind_ids = {}
    for o in PurchaseKind.objects.all():
        key = (o.name, o.position, o.unit_price)
        kind_ids.setdefault(key, []).append(o.id)
    for key, ids in kind_ids.items():
        if len(ids) == 1:
            print("Kind %s already coalesced" % (key,))
            continue
        ids.sort()
        main_id = ids[0]
        coalesce = ids[1:]
        coalesce_rel_qs = PurchaseKind.sheets.through.objects.filter(
            purchasekind_id__in=coalesce)
        coalesce_rel_qs.update(purchasekind_id=main_id)
        purchase_qs = Purchase.objects.filter(
            kind_id__in=coalesce)
        purchase_qs.update(kind_id=main_id)
        coalesce_qs = PurchaseKind.objects.filter(
            id__in=coalesce)
        print("Coalesce", key, coalesce_qs.delete())


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0010_purchasekind_meta'),
    ]

    operations = [
        migrations.RunPython(coalesce_kinds),
    ]
