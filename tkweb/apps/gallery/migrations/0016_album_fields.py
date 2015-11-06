# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0015_auto_20151106_0051'),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='eventalbum',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='album',
            name='publish_date',
            field=models.DateField(default=datetime.date(2015, 11, 5)),
        ),
        migrations.AddField(
            model_name='album',
            name='slug',
            field=models.SlugField(unique=True, default='test'),
            preserve_default=False,
        ),
    ]
