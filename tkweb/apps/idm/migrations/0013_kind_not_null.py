# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0012_set_title_kind'),
    ]

    operations = [
        migrations.AlterField(
            model_name='title',
            name='kind',
            field=models.CharField(choices=[('BEST', 'BEST'), ('FU', 'FU'), ('EFU', 'EFU')], max_length=10),
        ),
    ]
