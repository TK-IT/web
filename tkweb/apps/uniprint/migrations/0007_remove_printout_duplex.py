# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uniprint', '0006_populate_lp_option_string'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='printout',
            name='duplex',
        ),
    ]
