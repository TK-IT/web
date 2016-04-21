# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tkweb.apps.gallery.models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0005_file_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='GenericFile',
            fields=[
                ('basemedia_ptr', models.OneToOneField(primary_key=True, parent_link=True, to='gallery.BaseMedia', auto_created=True, serialize=False)),
                ('type', models.CharField(choices=[('V', 'Video'), ('A', 'Audio'), ('O', 'Other')], max_length=1, default='O')),
                ('file', models.FileField(upload_to=tkweb.apps.gallery.models.file_name)),
            ],
            bases=('gallery.basemedia',),
        ),
        migrations.RemoveField(
            model_name='file',
            name='basemedia_ptr',
        ),
        migrations.DeleteModel(
            name='File',
        ),
    ]
