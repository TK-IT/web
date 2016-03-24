# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0007_auto_20160323_0013'),
    ]

    operations = [
        migrations.AlterField(
            model_name='album',
            name='eventalbum',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='album',
            name='gfyear',
            field=models.PositiveSmallIntegerField(default=2015),
        ),
        migrations.AlterField(
            model_name='album',
            name='publish_date',
            field=models.DateField(default=datetime.date(2016, 3, 24), blank=True, null=True),
        ),
    ]
