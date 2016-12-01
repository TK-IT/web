# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0010_transaction_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='profile',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='session',
        ),
        migrations.DeleteModel(
            name='Payment',
        ),
    ]
