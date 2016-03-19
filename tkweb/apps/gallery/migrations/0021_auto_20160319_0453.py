# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0020_auto_20160319_0451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='album',
            name='slug',
            field=models.SlugField(),
        ),
        migrations.AlterUniqueTogether(
            name='album',
            unique_together=set([('gfyear', 'slug')]),
        ),
    ]
