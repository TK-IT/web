# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SheetStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('profile', models.ForeignKey(to='regnskab.Profile')),
            ],
        ),
    ]
