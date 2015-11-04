# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0002_image'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='album',
            options={'ordering': ['-gfyear']},
        ),
    ]
