# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0007_auto_20151104_1017'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='album',
            options={'ordering': ['-gfyear', 'order']},
        ),
    ]
