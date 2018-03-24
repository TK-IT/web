# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0011_coalesce_kinds'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchasekind',
            name='sheet',
        ),
    ]
