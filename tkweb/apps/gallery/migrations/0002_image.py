# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tkweb.apps.gallery.models
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
                ('image', sorl.thumbnail.fields.ImageField(upload_to=tkweb.apps.gallery.models.file_name)),
                ('caption', models.CharField(max_length=200, blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
    ]
