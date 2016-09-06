# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_profile_allow_direct_email(apps, schema_editor):
    Profile = apps.get_model('idm', 'Profile')
    qs1 = Profile.objects.filter(accepterdirektemail='ja')
    qs2 = Profile.objects.filter(accepterdirektemail='nej')
    assert qs1.count() + qs2.count() == Profile.objects.all().count()
    qs1.update(allow_direct_email=True)
    qs2.update(allow_direct_email=False)


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0026_profile_allow_direct_email'),
    ]

    operations = [
        migrations.RunPython(populate_profile_allow_direct_email),
    ]
