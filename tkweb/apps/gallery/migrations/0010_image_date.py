# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from datetime import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0009_auto_20151104_1100'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='date',
            field=models.DateTimeField(default=datetime.today()),
            preserve_default=False,
        ),
    ]
