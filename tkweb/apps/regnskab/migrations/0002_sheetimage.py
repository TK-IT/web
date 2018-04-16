# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import tkweb.apps.regnskab.models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SheetImage',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('page', models.PositiveIntegerField()),
                ('quad', jsonfield.fields.JSONField(default=[])),
                ('cols', jsonfield.fields.JSONField(default=[])),
                ('rows', jsonfield.fields.JSONField(default=[])),
                ('person_rows', jsonfield.fields.JSONField(default=[])),
                ('crosses', jsonfield.fields.JSONField(default=[])),
                ('person_counts', jsonfield.fields.JSONField(default=[])),
            ],
        ),
        migrations.AddField(
            model_name='sheet',
            name='image_file',
            field=models.FileField(upload_to=tkweb.apps.regnskab.models.sheet_upload_to, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sheet',
            name='row_image',
            field=models.FileField(upload_to=tkweb.apps.regnskab.models.sheet_upload_to, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sheet',
            name='row_image_width',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sheetrow',
            name='image_start',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sheetrow',
            name='image_stop',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sheetimage',
            name='sheet',
            field=models.ForeignKey(to='regnskab.Sheet'),
        ),
    ]
