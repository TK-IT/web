# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('regnskab', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='alias',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='alias',
            name='created_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 11, 14, 7, 6, 29, 883469, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='emailbatch',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='payment',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='payment',
            name='created_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 11, 14, 7, 6, 31, 927732, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sheet',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='sheet',
            name='created_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 11, 14, 7, 6, 33, 439700, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sheetstatus',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='sheetstatus',
            name='created_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 11, 14, 7, 6, 34, 775686, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
