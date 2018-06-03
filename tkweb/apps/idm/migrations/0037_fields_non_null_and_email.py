# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("idm", "0036_allow_matchtest_blank")]

    operations = [
        migrations.AlterField(
            model_name="group",
            name="name",
            field=models.CharField(max_length=25, default="", verbose_name="Navn"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="profile",
            name="country",
            field=models.CharField(
                verbose_name="Land", max_length=50, default="", blank=True
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="profile",
            name="email",
            field=models.EmailField(
                verbose_name="Emailadresse", max_length=50, default="", blank=True
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="profile",
            name="house_number",
            field=models.CharField(
                verbose_name="Husnr.", max_length=15, default="", blank=True
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="profile",
            name="name",
            field=models.CharField(max_length=50, default="", verbose_name="Navn"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="profile",
            name="note",
            field=models.TextField(default="", verbose_name="Note", blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="profile",
            name="phone_number",
            field=models.CharField(
                verbose_name="Telefonnr.", max_length=20, default="", blank=True
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="profile",
            name="postal_code",
            field=models.CharField(
                verbose_name="Postnr.", max_length=10, default="", blank=True
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="profile",
            name="street_name",
            field=models.CharField(
                verbose_name="Gade", max_length=50, default="", blank=True
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="profile",
            name="town",
            field=models.CharField(
                verbose_name="By", max_length=25, default="", blank=True
            ),
            preserve_default=False,
        ),
    ]
