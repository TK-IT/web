# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0009_auto_20160328_1956'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='notPublic',
            field=models.BooleanField(default=False),
        ),
    ]
