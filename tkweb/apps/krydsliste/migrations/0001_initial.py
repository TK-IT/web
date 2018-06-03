# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Sheet",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("title", models.TextField(blank=True)),
                ("left_label", models.TextField(blank=True)),
                ("right_label", models.TextField(blank=True)),
                ("column1", models.TextField(blank=True)),
                ("column2", models.TextField(blank=True)),
                ("column3", models.TextField(blank=True)),
                ("front_persons", models.TextField(blank=True)),
                ("back_persons", models.TextField(blank=True)),
                ("created_time", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        related_name="+",
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        )
    ]
