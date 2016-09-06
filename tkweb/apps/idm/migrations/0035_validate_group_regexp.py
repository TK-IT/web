# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import idm.models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0034_fix_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='regexp',
            field=models.CharField(max_length=50, verbose_name='Regulært udtryk', validators=[idm.models.validate_regex_pattern]),
        ),
    ]
