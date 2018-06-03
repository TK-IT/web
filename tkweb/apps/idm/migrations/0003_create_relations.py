# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("idm", "0002_manage_models")]

    operations = [
        migrations.CreateModel(
            name="GradGroupMembership",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("grad", models.IntegerField()),
                ("group", models.ForeignKey(to="idm.Group", on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name="Title",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("grad", models.IntegerField(null=True, blank=True)),
                ("orgtitel", models.CharField(max_length=10)),
                ("inttitel", models.CharField(max_length=10, null=True, blank=True)),
                (
                    "profile",
                    models.ForeignKey(to="idm.Profile", on_delete=models.CASCADE),
                ),
            ],
        ),
        migrations.AddField(
            model_name="profile",
            name="groups",
            field=models.ManyToManyField(to="idm.Group"),
        ),
        migrations.AddField(
            model_name="gradgroupmembership",
            name="profile",
            field=models.ForeignKey(to="idm.Profile", on_delete=models.CASCADE),
        ),
    ]
