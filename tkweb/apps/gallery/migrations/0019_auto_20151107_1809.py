# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0018_album_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='album',
            options={'ordering': ['gfyear', '-eventalbum', 'publish_date']},
        ),
        migrations.AddField(
            model_name='image',
            name='slug',
            field=models.SlugField(unique=True, default=datetime.datetime(2015, 11, 7, 17, 9, 10, 292356, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
