# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0010_image_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='image',
            options={'ordering': ['date']},
        ),
        migrations.AddField(
            model_name='album',
            name='eventalbum',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='album',
            name='publish_date',
            field=models.DateField(default=datetime.date(2015, 11, 6)),
        ),
        migrations.AddField(
            model_name='album',
            name='slug',
            field=models.SlugField(editable=False, default=1, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='image',
            name='date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
