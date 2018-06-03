# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("regnskab", "0006_cutoff_values")]

    operations = [
        migrations.AddField(
            model_name="alias",
            name="is_title",
            field=models.BooleanField(
                verbose_name="Primær titel",
                default=False,
                help_text="Markeres hvis aliaset skal vises foran personens navn som om det var en titel.",
            ),
        )
    ]
