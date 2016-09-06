# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def copy_membership(apps, schema_editor):
    Profile = apps.get_model('idm', 'Profile')
    GradGroupMembership = apps.get_model('idm', 'GradGroupMembership')
    Gruppemedlemmer = apps.get_model('idm', 'Gruppemedlemmer')
    Gradgruppemedlemmer = apps.get_model('idm', 'Gradgruppemedlemmer')

    a = []
    for o in Gruppemedlemmer.objects.values('gruppeid', 'personid'):
        a.append(Profile.groups.through(
            profile_id=o['personid'], group_id=o['gruppeid']))

    b = []
    qs = Gradgruppemedlemmer.objects.values(
        'personid', 'grad', 'gruppeid')
    for o in qs:
        b.append(GradGroupMembership(
            profile_id=o['personid'], group_id=o['gruppeid'], grad=o['grad']))

    Profile.groups.through.objects.bulk_create(a)
    GradGroupMembership.objects.bulk_create(b)


def copy_titles(apps, schema_editor):
    Title = apps.get_model('idm', 'Title')
    Titler = apps.get_model('idm', 'Titler')

    a = []
    for o in Titler.objects.values('personid', 'grad', 'orgtitel', 'inttitel'):
        a.append(Title(
            profile_id=o['personid'], grad=o['grad'],
            orgtitel=o['orgtitel'], inttitel=o['inttitel']))

    Title.objects.bulk_create(a)


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0003_create_relations'),
    ]

    operations = [
        migrations.RunPython(copy_membership),
        migrations.RunPython(copy_titles),
    ]
