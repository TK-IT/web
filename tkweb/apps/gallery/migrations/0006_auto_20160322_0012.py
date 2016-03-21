# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0005_auto_20160322_0008'),
    ]

    operations = [
        migrations.AlterField(
            model_name='album',
            name='publish_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
