# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0004_auto_20151104_1001'),
    ]

    operations = [
        migrations.AlterField(
            model_name='album',
            name='gfyear',
            field=models.PositiveSmallIntegerField(),
        ),
    ]
