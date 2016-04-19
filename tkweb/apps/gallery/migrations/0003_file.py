# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tkweb.apps.gallery.models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0002_auto_20160419_1331'),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('basemedia_ptr', models.OneToOneField(auto_created=True, to='gallery.BaseMedia', serialize=False, primary_key=True, parent_link=True)),
                ('file', models.FileField(upload_to=tkweb.apps.gallery.models.file_name)),
            ],
            bases=('gallery.basemedia',),
        ),
    ]
