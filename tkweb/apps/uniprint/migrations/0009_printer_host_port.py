# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2021-11-30 16:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uniprint', '0008_printout_output'),
    ]

    operations = [
        migrations.AddField(
            model_name='printer',
            name='hostname',
            field=models.CharField(default='localhost', max_length=100),
        ),
        migrations.AddField(
            model_name='printer',
            name='port',
            field=models.IntegerField(default=631),
        ),
    ]