# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0012_auto_20151106_0037'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='image',
            options={'ordering': ['date']},
        ),
    ]
