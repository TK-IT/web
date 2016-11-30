# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0007_session_period'),
    ]

    operations = [
        migrations.RenameField(
            model_name='purchasekind',
            old_name='price',
            new_name='unit_price',
        ),
    ]
