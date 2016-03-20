# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0003_auto_20160321_0032'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='image',
            options={'ordering': ['date', 'slug']},
        ),
    ]
