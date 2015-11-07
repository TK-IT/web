# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0017_album_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='album',
            options={'ordering': ['gfyear', 'publish_date']},
        ),
        migrations.RemoveField(
            model_name='album',
            name='order',
        ),
        migrations.AlterField(
            model_name='album',
            name='eventalbum',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='album',
            name='publish_date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='album',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]
