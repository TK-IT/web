# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tkweb.apps.gallery.models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0008_auto_20160324_1158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='album',
            name='gfyear',
            field=models.PositiveSmallIntegerField(default=tkweb.apps.gallery.models.get_gfyear),
        ),
        migrations.AlterField(
            model_name='album',
            name='publish_date',
            field=models.DateField(blank=True, default=datetime.date.today, null=True),
        ),
    ]
