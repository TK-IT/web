# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.db.models import Q


def remove_funny_titles(apps, schema_editor):
    Title = apps.get_model('idm', 'Title')
    qs = Title.objects.all()
    for t in 'CERM FORM INKA KASS NF PR SEKR VC TVC BEST EFUIT'.split():
        qs = qs.filter(~Q(orgtitel=t))
    qs = qs.filter(~Q(orgtitel__startswith='FU'))
    qs = qs.filter(~Q(orgtitel='EFUHU'))

    funny_titles = [t.orgtitel for t in qs]
    if funny_titles:
        if funny_titles != ['OFULD']:
            raise ValueError(funny_titles)
        # Sorry, Sune
        qs.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0009_rename_tables'),
    ]

    operations = [
        migrations.RunPython(remove_funny_titles,
                             lambda apps, schema_editor: None),
    ]
