# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0002_auto_20160320_2009'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='image',
            unique_together=set([('album', 'slug')]),
        ),
    ]
