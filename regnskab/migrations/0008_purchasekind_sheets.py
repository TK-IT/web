# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0007_alias_is_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasekind',
            name='sheets',
            field=models.ManyToManyField(related_name='_purchasekind_sheets_+', to='regnskab.Sheet'),
        ),
    ]
