# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def add_mailing_list_group(apps, schema_editor):
    Group = apps.get_model('idm', 'Group')
    Profile = apps.get_model('idm', 'Profile')
    # Cannot access Group.REGEXP_MAILING_LIST from here :-(
    g = Group(name='Hængerlisten', regexp='no$public$address')
    existing = list(Group.objects.filter(regexp=g.regexp))
    if existing:
        raise ValueError(existing)
    g.save()

    qs = Profile.objects.filter(accepteremail='ja')

    # Bulk add everyone in qs to Group.profile_set
    relations = [Profile.groups.through(group_id=g.id, profile_id=i)
                 for i, in qs.values_list('id')]
    if relations:
        Profile.groups.through.objects.bulk_create(relations)
    else:
        raise ValueError("No people added to %s" % (g,))


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0023_rename_fields'),
    ]

    operations = [
        migrations.RunPython(add_mailing_list_group),
    ]
