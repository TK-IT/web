# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uniprint', '0004_set_document_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='printout',
            name='lp_option_string',
            field=models.TextField(blank=True),
        ),
    ]
