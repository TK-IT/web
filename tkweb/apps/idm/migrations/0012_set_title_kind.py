# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.db.models import Q


def set_title_kind(apps, schema_editor):
    Title = apps.get_model('idm', 'Title')

    best = Q(orgtitel='BEST')
    for t in 'CERM FORM INKA KASS NF PR SEKR VC TVC BEST'.split():
        best = best | Q(orgtitel=t)

    fu = Q(orgtitel__startswith='FU') | Q(orgtitel='EFUHU')

    efu = Q(orgtitel='EFUIT')

    others = list(Title.objects.filter(~best & ~fu & ~efu))
    if others:
        raise ValueError(others)

    # Cannot access Title.BEST et al here :-(
    Title.objects.filter(best).update(kind='BEST')
    Title.objects.filter(fu).update(kind='FU')
    Title.objects.filter(efu).update(kind='EFU')

    assert not Title.objects.filter(kind=None).exists()


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0011_title_kind'),
    ]

    operations = [
        migrations.RunPython(set_title_kind),
    ]
