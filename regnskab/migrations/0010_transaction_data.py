# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def copy_data(from_model, to_model):
    fields = set(f.name for f in from_model._meta.fields) - {'kind'}
    set_kind = any(f.name == 'kind' for f in to_model._meta.fields)
    objects = []
    for o in from_model.objects.all():
        data = {k: getattr(o, k)
                for k in fields}
        data['amount'] = -data['amount']
        if set_kind:
            data['kind'] = 'payment' if data['amount'] < 0 else 'purchase'
        objects.append(to_model(**data))
    to_model.objects.bulk_create(objects)
    from_model.objects.all().delete()


def copy_payment_to_transaction(apps, schema_editor):
    return copy_data(apps.get_model('regnskab', 'Payment'),
                     apps.get_model('regnskab', 'Transaction'))


def copy_transaction_to_payment(apps, schema_editor):
    return copy_data(apps.get_model('regnskab', 'Transaction'),
                     apps.get_model('regnskab', 'Payment'))


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0009_transaction'),
    ]

    operations = [
        migrations.RunPython(copy_payment_to_transaction,
                             copy_transaction_to_payment),
    ]
