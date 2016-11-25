# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0005_rename_batch_session'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='session',
            name='payment_set',
        ),
        migrations.RemoveField(
            model_name='session',
            name='sheet_set',
        ),
        migrations.AddField(
            model_name='payment',
            name='session',
            field=models.ForeignKey(to='regnskab.Session', null=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AddField(
            model_name='sheet',
            name='session',
            field=models.ForeignKey(to='regnskab.Session', null=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
    ]
