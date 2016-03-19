# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0019_auto_20151107_1809'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
