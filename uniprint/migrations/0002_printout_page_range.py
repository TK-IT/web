# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uniprint', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='printout',
            name='page_range',
            field=models.CharField(default='', blank=True, max_length=255),
        ),
    ]
