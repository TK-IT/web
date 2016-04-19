# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0003_file'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='basemedia',
            options={'ordering': ['forcedOrder', 'date', 'slug']},
        ),
        migrations.AddField(
            model_name='basemedia',
            name='forcedOrder',
            field=models.SmallIntegerField(default=0, validators=[django.core.validators.MinValueValidator(-10000), django.core.validators.MaxValueValidator(10000)]),
        ),
    ]
