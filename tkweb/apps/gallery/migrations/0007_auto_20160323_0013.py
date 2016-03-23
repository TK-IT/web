# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tkweb.apps.gallery.models
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0006_auto_20160322_0012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='image',
            field=versatileimagefield.fields.VersatileImageField(upload_to=tkweb.apps.gallery.models.file_name),
        ),
    ]
