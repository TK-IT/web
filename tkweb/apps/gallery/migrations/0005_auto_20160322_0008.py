# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0004_auto_20160321_0038'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='album',
            options={'ordering': ['gfyear', '-eventalbum', 'oldFolder', 'publish_date']},
        ),
        migrations.AddField(
            model_name='album',
            name='oldFolder',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
