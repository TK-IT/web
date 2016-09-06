# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0028_remove_profile_accepterdirektemail'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='gone',
            new_name='gone_janej',
        ),
    ]
