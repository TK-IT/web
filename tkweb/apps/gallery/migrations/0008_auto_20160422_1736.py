# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0007_auto_20160422_1729'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basemedia',
            name='slug',
            field=models.SlugField(blank=True, null=True),
        ),
    ]
