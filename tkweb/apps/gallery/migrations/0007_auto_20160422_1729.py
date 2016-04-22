# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tkweb.apps.gallery.models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0006_auto_20160421_1046'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='genericfile',
            name='type',
        ),
        migrations.AddField(
            model_name='basemedia',
            name='type',
            field=models.CharField(max_length=1, choices=[('I', 'Image'), ('V', 'Video'), ('A', 'Audio'), ('O', 'Other')], default='O'),
        ),
    ]
