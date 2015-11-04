# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0005_auto_20151104_1011'),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='order',
            field=models.PositiveSmallIntegerField(default=1),
            preserve_default=False,
        ),
    ]
