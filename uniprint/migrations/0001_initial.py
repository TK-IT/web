# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('file', models.FileField(upload_to='')),
                ('original_filename', models.CharField(max_length=255)),
                ('text', models.TextField(null=True, blank=True)),
                ('pages', models.IntegerField()),
                ('pdfinfo', models.TextField(null=True, blank=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_time'],
            },
        ),
        migrations.CreateModel(
            name='Printer',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('destination', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Printout',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('copies', models.PositiveIntegerField(default=1)),
                ('duplex', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to=settings.AUTH_USER_MODEL)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to='uniprint.Document')),
                ('printer', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to='uniprint.Printer')),
            ],
        ),
    ]
