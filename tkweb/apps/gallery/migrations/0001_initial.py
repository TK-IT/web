# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import sorl.thumbnail.fields
import tkweb.apps.gallery.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('publish_date', models.DateField()),
                ('eventalbum', models.BooleanField()),
                ('gfyear', models.PositiveSmallIntegerField()),
                ('slug', models.SlugField()),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['gfyear', '-eventalbum', 'publish_date'],
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('image', sorl.thumbnail.fields.ImageField(upload_to=tkweb.apps.gallery.models.file_name)),
                ('date', models.DateTimeField(blank=True, null=True)),
                ('caption', models.CharField(max_length=200, blank=True)),
                ('slug', models.SlugField(unique=True)),
                ('album', models.ForeignKey(related_name='images', to='gallery.Album')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='album',
            unique_together=set([('gfyear', 'slug')]),
        ),
    ]
