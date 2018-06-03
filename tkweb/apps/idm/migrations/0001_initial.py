# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Adresser",
            fields=[
                ("id", models.IntegerField(serialize=False, primary_key=True)),
                ("gade", models.CharField(max_length=50)),
                ("husnr", models.CharField(max_length=15)),
                ("postnr", models.CharField(max_length=10)),
                ("postby", models.CharField(max_length=25)),
                ("land", models.CharField(max_length=25)),
                ("tlf", models.CharField(max_length=15)),
                ("gone", models.IntegerField()),
            ],
            options={"db_table": "adresser"},
        ),
        migrations.CreateModel(
            name="Andenbruger",
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
                ("login", models.CharField(max_length=32, null=True, blank=True)),
                ("password", models.CharField(max_length=32, null=True, blank=True)),
                ("type", models.CharField(max_length=10, null=True, blank=True)),
            ],
            options={"db_table": "andenbruger"},
        ),
        migrations.CreateModel(
            name="Arrangementer",
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
                ("titel", models.CharField(max_length=50, null=True, blank=True)),
                ("dag", models.IntegerField(null=True, blank=True)),
                ("maned", models.IntegerField(null=True, blank=True)),
                ("ar", models.IntegerField(null=True, blank=True)),
                ("beskrivelse", models.TextField(null=True, blank=True)),
            ],
            options={"db_table": "arrangementer"},
        ),
        migrations.CreateModel(
            name="Best",
            fields=[
                ("sortid", models.IntegerField(serialize=False, primary_key=True)),
                ("orgtitel", models.CharField(max_length=50)),
                ("titel", models.CharField(max_length=10)),
            ],
            options={"db_table": "best"},
        ),
        migrations.CreateModel(
            name="Bestyrelsen",
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
                ("titel", models.CharField(max_length=5, null=True, blank=True)),
                ("navn", models.CharField(max_length=50, null=True, blank=True)),
                ("adresse1", models.CharField(max_length=50, null=True, blank=True)),
                ("adresse2", models.CharField(max_length=50, null=True, blank=True)),
                ("postnr", models.IntegerField(null=True, blank=True)),
                ("postby", models.CharField(max_length=25, null=True, blank=True)),
                ("dag", models.IntegerField(null=True, blank=True)),
                ("maned", models.IntegerField(null=True, blank=True)),
                ("ar", models.IntegerField(null=True, blank=True)),
                ("stdtlf", models.IntegerField(null=True, blank=True)),
                ("mbltlf", models.IntegerField(null=True, blank=True)),
                ("arskort", models.IntegerField(null=True, blank=True)),
                ("email", models.CharField(max_length=50, null=True, blank=True)),
                ("hjemmeside", models.CharField(max_length=50, null=True, blank=True)),
            ],
            options={"db_table": "bestyrelsen"},
        ),
        migrations.CreateModel(
            name="Bestyrelsenold",
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
                ("titel", models.CharField(max_length=5, null=True, blank=True)),
                ("navn", models.CharField(max_length=50, null=True, blank=True)),
                ("adresse1", models.CharField(max_length=50, null=True, blank=True)),
                ("adresse2", models.CharField(max_length=50, null=True, blank=True)),
                ("postnr", models.IntegerField(null=True, blank=True)),
                ("postby", models.CharField(max_length=25, null=True, blank=True)),
                ("dag", models.IntegerField(null=True, blank=True)),
                ("maned", models.IntegerField(null=True, blank=True)),
                ("ar", models.IntegerField(null=True, blank=True)),
                ("stdtlf", models.IntegerField(null=True, blank=True)),
                ("mbltlf", models.IntegerField(null=True, blank=True)),
                ("arskort", models.IntegerField(null=True, blank=True)),
                ("email", models.CharField(max_length=50, null=True, blank=True)),
                ("hjemmeside", models.CharField(max_length=50, null=True, blank=True)),
            ],
            options={"db_table": "bestyrelsenOLD"},
        ),
        migrations.CreateModel(
            name="Bruger",
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
                ("login", models.CharField(max_length=32, null=True, blank=True)),
                ("password", models.CharField(max_length=32, null=True, blank=True)),
            ],
            options={"db_table": "bruger"},
        ),
        migrations.CreateModel(
            name="Gradgruppemedlemmer",
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
                ("personid", models.IntegerField(null=True, blank=True)),
                ("grad", models.IntegerField(null=True, blank=True)),
                ("gruppeid", models.IntegerField()),
            ],
            options={"db_table": "gradgruppemedlemmer"},
        ),
        migrations.CreateModel(
            name="Group",
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
                ("navn", models.CharField(max_length=25, null=True, blank=True)),
                ("regexp", models.CharField(max_length=50)),
                ("matchtest", models.TextField()),
                ("relativ", models.IntegerField()),
                ("type", models.IntegerField()),
            ],
            options={"db_table": "grupper"},
        ),
        migrations.CreateModel(
            name="Gruppemedlemmer",
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
                ("gruppeid", models.IntegerField(null=True, blank=True)),
                ("personid", models.IntegerField(null=True, blank=True)),
            ],
            options={"db_table": "gruppemedlemmer"},
        ),
        migrations.CreateModel(
            name="Grupperold",
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
                ("navn", models.CharField(max_length=25, null=True, blank=True)),
                ("regexp", models.CharField(max_length=50)),
                ("matchtest", models.TextField()),
                ("relativ", models.IntegerField()),
                ("type", models.IntegerField()),
            ],
            options={"db_table": "grupperOLD"},
        ),
        migrations.CreateModel(
            name="Grupperv2Old",
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
                ("navn", models.CharField(max_length=25, null=True, blank=True)),
                ("regexp", models.CharField(max_length=50)),
                ("matchtest", models.TextField()),
                ("relativ", models.IntegerField()),
                ("type", models.IntegerField()),
            ],
            options={"db_table": "grupperV2OLD"},
        ),
        migrations.CreateModel(
            name="J50Adr",
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
                ("periode", models.CharField(max_length=5, null=True, blank=True)),
                ("orgtitel", models.CharField(max_length=5, null=True, blank=True)),
                ("vistnok", models.IntegerField(null=True, blank=True)),
                ("navn", models.CharField(max_length=50, null=True, blank=True)),
                ("gade", models.CharField(max_length=50, null=True, blank=True)),
                ("husnr", models.CharField(max_length=15, null=True, blank=True)),
                ("postnr", models.CharField(max_length=10, null=True, blank=True)),
                ("postby", models.CharField(max_length=25, null=True, blank=True)),
                ("email", models.CharField(max_length=50, null=True, blank=True)),
                ("bekraft", models.IntegerField(null=True, blank=True)),
                ("periode2", models.CharField(max_length=5, null=True, blank=True)),
                ("orgtitel2", models.CharField(max_length=5, null=True, blank=True)),
                ("gone", models.IntegerField(null=True, blank=True)),
                ("vistnok2", models.CharField(max_length=5, null=True, blank=True)),
                ("tlf", models.CharField(max_length=15, null=True, blank=True)),
                ("note", models.TextField(null=True, blank=True)),
                ("tilmeld", models.IntegerField(null=True, blank=True)),
            ],
            options={"db_table": "j50adr"},
        ),
        migrations.CreateModel(
            name="J50AdrOld",
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
                ("periode", models.CharField(max_length=5, null=True, blank=True)),
                ("orgtitel", models.CharField(max_length=5, null=True, blank=True)),
                ("vistnok", models.IntegerField(null=True, blank=True)),
                ("navn", models.CharField(max_length=50, null=True, blank=True)),
                ("gade", models.CharField(max_length=50, null=True, blank=True)),
                ("husnr", models.CharField(max_length=15, null=True, blank=True)),
                ("postnr", models.CharField(max_length=10, null=True, blank=True)),
                ("postby", models.CharField(max_length=25, null=True, blank=True)),
                ("email", models.CharField(max_length=50, null=True, blank=True)),
                ("bekraft", models.IntegerField(null=True, blank=True)),
                ("periode2", models.CharField(max_length=5, null=True, blank=True)),
                ("orgtitel2", models.CharField(max_length=5, null=True, blank=True)),
                ("gone", models.IntegerField(null=True, blank=True)),
                ("vistnok2", models.CharField(max_length=5, null=True, blank=True)),
                ("tlf", models.CharField(max_length=15, null=True, blank=True)),
                ("note", models.TextField(null=True, blank=True)),
                ("tilmeld", models.IntegerField(null=True, blank=True)),
            ],
            options={"db_table": "j50adr-OLD"},
        ),
        migrations.CreateModel(
            name="J50Arr",
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
                ("titel", models.CharField(max_length=25, null=True, blank=True)),
                ("dag", models.IntegerField(null=True, blank=True)),
                ("fra", models.IntegerField(null=True, blank=True)),
                ("til", models.IntegerField(null=True, blank=True)),
                ("skema", models.IntegerField(null=True, blank=True)),
                ("arrangement", models.TextField(null=True, blank=True)),
            ],
            options={"db_table": "j50arr"},
        ),
        migrations.CreateModel(
            name="Lokaldata",
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
                ("navn", models.CharField(unique=True, max_length=10)),
                ("data", models.TextField()),
            ],
            options={"db_table": "lokalData"},
        ),
        migrations.CreateModel(
            name="Mylog",
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
                ("sec", models.IntegerField(null=True, blank=True)),
                ("min", models.IntegerField(null=True, blank=True)),
                ("hour", models.IntegerField(null=True, blank=True)),
                ("day", models.IntegerField(null=True, blank=True)),
                ("month", models.IntegerField(null=True, blank=True)),
                ("year", models.IntegerField(null=True, blank=True)),
                ("action", models.TextField(null=True, blank=True)),
            ],
            options={"db_table": "mylog"},
        ),
        migrations.CreateModel(
            name="Nyheder",
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
                ("dag", models.IntegerField(null=True, blank=True)),
                ("maned", models.IntegerField(null=True, blank=True)),
                ("ar", models.IntegerField(null=True, blank=True)),
                ("beskrivelse", models.TextField(null=True, blank=True)),
            ],
            options={"db_table": "nyheder"},
        ),
        migrations.CreateModel(
            name="Profile",
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
                ("navn", models.CharField(max_length=50, null=True, blank=True)),
                ("email", models.CharField(max_length=50, null=True, blank=True)),
                (
                    "accepteremail",
                    models.CharField(max_length=3, null=True, blank=True),
                ),
                (
                    "accepterdirektemail",
                    models.CharField(max_length=3, null=True, blank=True),
                ),
                ("gade", models.CharField(max_length=50, null=True, blank=True)),
                ("husnr", models.CharField(max_length=15, null=True, blank=True)),
                ("postnr", models.CharField(max_length=10, null=True, blank=True)),
                ("postby", models.CharField(max_length=25, null=True, blank=True)),
                ("land", models.CharField(max_length=50, null=True, blank=True)),
                ("gone", models.CharField(max_length=3, null=True, blank=True)),
                ("tlf", models.CharField(max_length=20, null=True, blank=True)),
                ("note", models.TextField(null=True, blank=True)),
            ],
            options={"db_table": "tkfolk"},
        ),
        migrations.CreateModel(
            name="Titler",
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
                ("personid", models.IntegerField(null=True, blank=True)),
                ("grad", models.IntegerField(null=True, blank=True)),
                ("orgtitel", models.CharField(max_length=10, null=True, blank=True)),
                ("inttitel", models.CharField(max_length=10, null=True, blank=True)),
            ],
            options={"db_table": "titler"},
        ),
        migrations.CreateModel(
            name="Tkfolkbackup",
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
                ("navn", models.CharField(max_length=50, null=True, blank=True)),
                ("email", models.CharField(max_length=50, null=True, blank=True)),
                (
                    "accepteremail",
                    models.CharField(max_length=3, null=True, blank=True),
                ),
            ],
            options={"db_table": "tkfolkBACKUP"},
        ),
        migrations.CreateModel(
            name="Tkfolkfix",
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
                ("navn", models.CharField(max_length=50, null=True, blank=True)),
                ("email", models.CharField(max_length=50, null=True, blank=True)),
                (
                    "accepteremail",
                    models.CharField(max_length=3, null=True, blank=True),
                ),
            ],
            options={"db_table": "tkfolkFix"},
        ),
        migrations.CreateModel(
            name="TkfolkOld",
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
                ("navn", models.CharField(max_length=50, null=True, blank=True)),
                ("email", models.CharField(max_length=50, null=True, blank=True)),
                (
                    "accepteremail",
                    models.CharField(max_length=3, null=True, blank=True),
                ),
            ],
            options={"db_table": "tkfolk-OLD"},
        ),
    ]
