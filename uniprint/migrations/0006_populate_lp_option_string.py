# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def populate_lp_option_string(apps, schema_editor):
    Printout = apps.get_model('uniprint', 'Printout')
    for p in Printout.objects.all():
        if p.duplex:
            p.lp_option_string = '-o Duplex=DuplexNoTumble'
        else:
            p.lp_option_string = '-o Duplex=None'
        p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('uniprint', '0005_printout_lp_option_string'),
    ]

    operations = [
        migrations.RunPython(populate_lp_option_string),
    ]
