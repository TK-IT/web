# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0004_session'),
    ]

    operations = [
        migrations.RenameField(
            model_name='email',
            old_name='batch',
            new_name='session',
        ),
    ]
