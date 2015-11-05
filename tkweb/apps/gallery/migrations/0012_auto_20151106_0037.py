# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tkweb.apps.gallery.models
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0011_auto_20151106_0015'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='image',
            field=sorl.thumbnail.fields.ImageField(upload_to=tkweb.apps.gallery.models.file_name),
        ),
    ]
