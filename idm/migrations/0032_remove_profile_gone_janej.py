# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0031_populate_profile_gone'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='gone_janej',
        ),
    ]
