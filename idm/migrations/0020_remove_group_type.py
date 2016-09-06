# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0019_remove_useless_groups'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='type',
        ),
    ]
