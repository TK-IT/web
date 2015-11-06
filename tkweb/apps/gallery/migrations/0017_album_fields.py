# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0016_album_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='album',
            name='publish_date',
            field=models.DateField(default=datetime.date(2015, 11, 6)),
        ),
        migrations.AlterField(
            model_name='album',
            name='slug',
            field=models.SlugField(unique=True, editable=False),
        ),
    ]
