# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0004_auto_20160419_1456'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='type',
            field=models.CharField(max_length=1, choices=[('V', 'Video'), ('A', 'Audio'), ('O', 'Other')], default='O'),
        ),
    ]
