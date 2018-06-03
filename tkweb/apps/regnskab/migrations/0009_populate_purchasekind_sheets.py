# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def populate_purchasekind_sheets(apps, schema_editor):
    PurchaseKind = apps.get_model("regnskab", "PurchaseKind")
    existing_qs = PurchaseKind.sheets.through.objects.all()
    existing = set(existing_qs.values_list("purchasekind_id", "sheet_id"))
    old_rels = set(PurchaseKind.objects.all().values_list("id", "sheet_id"))
    create = [
        PurchaseKind.sheets.through(purchasekind_id=kind_id, sheet_id=sheet_id)
        for kind_id, sheet_id in old_rels - existing
    ]
    PurchaseKind.sheets.through.objects.bulk_create(create)


class Migration(migrations.Migration):

    dependencies = [("regnskab", "0008_purchasekind_sheets")]

    operations = [migrations.RunPython(populate_purchasekind_sheets)]
