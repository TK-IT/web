# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_profile_gone(apps, schema_editor):
    Profile = apps.get_model('idm', 'Profile')
    qs1 = Profile.objects.filter(gone_janej='ja')
    qs2 = Profile.objects.filter(gone_janej='nej')
    assert qs1.count() + qs2.count() == Profile.objects.all().count()
    qs1.update(gone=True)
    qs2.update(gone=False)


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0030_profile_gone'),
    ]

    operations = [
        migrations.RunPython(populate_profile_gone,
                             lambda apps, schema_editor: None),
    ]
