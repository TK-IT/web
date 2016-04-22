# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tkweb.apps.gallery.models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0008_auto_20160422_1736'),
    ]

    operations = [
        migrations.AddField(
            model_name='genericfile',
            name='originalFile',
            field=models.FileField(upload_to=tkweb.apps.gallery.models.file_name, blank=True),
        ),
    ]
