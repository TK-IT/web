# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0006_move_relation_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='period',
            field=models.IntegerField(verbose_name='Årgang', default=2016),
            preserve_default=False,
        ),
    ]
