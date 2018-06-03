# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("regnskab", "0016_html_email")]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="email",
                    name="session",
                    field=models.ForeignKey(
                        related_name="email_set", to="regnskab.Session"
                    ),
                )
            ]
        )
    ]
