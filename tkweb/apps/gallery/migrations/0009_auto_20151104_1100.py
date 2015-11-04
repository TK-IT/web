# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tkweb.apps.gallery.models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0008_auto_20151104_1019'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='album',
            options={'ordering': ['gfyear', 'order']},
        ),
        migrations.AlterField(
            model_name='album',
            name='gfyear',
            field=models.PositiveSmallIntegerField(default=tkweb.apps.gallery.models.Album.nextGfyear),
        ),
        migrations.AlterField(
            model_name='album',
            name='order',
            field=models.PositiveSmallIntegerField(default=tkweb.apps.gallery.models.Album.nextOrder),
        ),
    ]
