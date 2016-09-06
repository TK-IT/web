# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.db.models import F


def populate_title_period(apps, schema_editor):
    Title = apps.get_model('idm', 'Title')
    try:
        jonas = Title.objects.get(profile__navn='Wouter Boomsma')
        current_period = 2000 + jonas.grad
    except Title.DoesNotExist:
        current_period = 2015
    Title.objects.all().update(period=current_period - F('grad'))


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0015_title_period'),
    ]

    operations = [
        migrations.RunPython(populate_title_period,
                             lambda apps, schema_editor: None),
    ]
