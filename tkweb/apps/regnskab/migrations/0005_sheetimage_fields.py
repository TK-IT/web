# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("regnskab", "0004_quad_shape"),
    ]

    operations = [
        migrations.AddField(
            model_name="sheetimage",
            name="boxes",
            field=jsonfield.fields.JSONField(default=[]),
        ),
        migrations.AddField(
            model_name="sheetimage",
            name="verified_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="sheetimage",
            name="verified_time",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
