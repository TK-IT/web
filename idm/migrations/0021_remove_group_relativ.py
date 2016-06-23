# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0020_remove_group_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='relativ',
        ),
    ]
