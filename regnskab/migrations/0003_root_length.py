# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0002_creator_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alias',
            name='root',
            field=models.CharField(verbose_name='Alias', max_length=200),
        ),
    ]
