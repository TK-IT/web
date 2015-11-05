# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tkweb.apps.gallery.models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0010_image_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ImageField(upload_to=tkweb.apps.gallery.models.file_name),
        ),
    ]
