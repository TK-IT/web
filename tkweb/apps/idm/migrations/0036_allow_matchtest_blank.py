# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0035_validate_group_regexp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='matchtest',
            field=models.TextField(blank=True, verbose_name='Eksempler'),
        ),
    ]
